import datetime
import logging
import os
import pkgutil
import re
import subprocess

from lab import tools
from lab.environments import Environment


def fill_template(template_name, **parameters):
    template = tools.get_string(
        pkgutil.get_data("lab_htcondor_environment",
                          os.path.join("data", template_name + ".template"))
    )
    return template % parameters


class HTCondorEnvironment(Environment):
    """
    Environment for running experiments in a HTCondor cluster.
    """

    EXP_RUN_SCRIPT = "condor.submit"

    def __init__(
        self,
        nice_user="True",
        email="",
        notification_mode="Never",
        getenv="True",
        priority=0,
        universe="vanilla",
        request_memory="0",
        requirements_line="",
        custom_lines="",
        **kwargs,
    ):
        """
        The HTCondor job parameters.

        As `requirements_line` the full requirements line
        (including 'requirements = ') can be specified.

        As `custom_lines` a string specifying other commands can be inserted.

        See :py:class:`~lab.environments.Environment` for inherited
        parameters.
        """
        Environment.__init__(self, **kwargs)

        self.nice_user = nice_user
        self.email = email
        self.notification_mode = notification_mode
        self.getenv = getenv
        self.priority = priority
        self.requirements_line = requirements_line
        self.universe = universe
        self.request_memory = request_memory
        self.custom_lines = custom_lines

    def _create_symlinks(self):
        """
        Create a plain directories structure of symbolic links pointing to the actual
        lab directories structure to be used by HTCondor, since HTCondor job files only
        admit a process number as variable for the initial directory.
        """
        from lab.experiment import get_run_dir

        symlinks_root = os.path.join(self.exp.path, "condor_plain_tree_structure")
        os.makedirs(symlinks_root)
        for i in range(len(self.exp.runs)):
            os.symlink(
                os.path.join("..", get_run_dir(i + 1)),
                os.path.join(symlinks_root, str(i)),
            )

    def _get_code_dirs(self):
        return ",".join(
            [
                f"../../code-{cached_rev.name}"
                for cached_rev in self.exp._get_unique_cached_revisions()
            ]
        )

    def _create_requirements_file(self):
        out = subprocess.check_output(["pip", "freeze"])
        with open(os.path.join(self.exp.path, "requirements.txt"), "w") as outp:
            outp.write(out.decode())

    def _create_patched_run_files(self):
        """
        Create a patched run file for each experiment exactly equal than the
        original one but using the python3 executable from the path and
        removing all relative paths because all files are in the same directory
        in the cluster nodes.
        """
        from lab.experiment import get_run_dir

        absolute_path_regex = re.compile(r"'/.+/")
        code_path_regex = re.compile(r"'/.+/code-")

        for i in range(len(self.exp.runs)):
            run_dir = os.path.join(self.exp.path, get_run_dir(i + 1))
            patched_run = os.path.join(run_dir, "patched_run")
            with open(os.path.join(run_dir, "run")) as inp:
                with open(patched_run, "w") as outp:
                    for line in inp:
                        line = line.replace(
                                tools.get_python_executable(), "python3"
                            ).replace("../../", "")
                        line = code_path_regex.sub("'code-", line)
                        line = absolute_path_regex.sub("'", line)
                        outp.write(line)

            os.chmod(patched_run, 0o755)

    def _create_condor_run_files(self):
        """
        Create a executable for each experiment doing the following:
        1. Create a virtual environment.
        2. Activate the created virtual environment.
        3. Install the `requirements.txt` file in the virtual environment.
        4. Execute the `patched_run` script.
        5. Deactivate the virtual environment.
        6. Remove the virtual environment to avoid transferring it to the caller.
        """
        from lab.experiment import get_run_dir

        for i in range(len(self.exp.runs)):
            run_dir = os.path.join(self.exp.path, get_run_dir(i + 1))
            condor_run = os.path.join(run_dir, "condor_run")
            with open(condor_run, "w") as outp:
                outp.write("#!/bin/bash\n")
                outp.write("python3 -m venv .venv\n")
                outp.write("source .venv/bin/activate\n")
                outp.write("pip install -r requirements.txt\n")
                outp.write("./run_task.py\n")
                outp.write("deactivate\n")
                outp.write("rm -rf .venv\n")

            os.chmod(condor_run, 0o755)

    def _create_run_task_files(self):
        from lab.experiment import get_run_dir

        for i in range(len(self.exp.runs)):
            task_id = i + 1
            run_task = fill_template(
                "ht_condor_run_task.py",
                task_id=task_id,
            )

            run_dir = os.path.join(self.exp.path, get_run_dir(task_id))
            run_file = os.path.join(run_dir, "run_task.py")
            with open(run_file, "w") as outp:
                outp.write(run_task)

            os.chmod(run_file, 0o755)

    def write_main_script(self):
        """
        Create a directory tree of symbolic links and then generate a HTCondor job file.
        """
        self._create_symlinks()

        code_dirs = self._get_code_dirs()
        self._create_requirements_file()
        self._create_patched_run_files()
        self._create_run_task_files()
        self._create_condor_run_files()

        # Get parsers paths from the experiment
        parsers = ""
        for resource in self.exp.resources:
            if resource.is_parser:
                parser_filename = self.exp.env_vars_relative[resource.name]
                rel_parser = os.path.join("../../", parser_filename)
                parsers += f"\n{rel_parser}, \\"

        script = fill_template(
            "htcondor-job",
            datetime=datetime.datetime.now().isoformat(),
            nice_user=self.nice_user,
            email=self.email,
            notification_mode=self.notification_mode,
            getenv=self.getenv,
            priority=self.priority,
            requirements_line=self.requirements_line,
            universe=self.universe,
            request_memory=self.request_memory,
            custom_lines=self.custom_lines,
            n_tasks=len(self.exp.runs),
            parsers=parsers,
            code_dirs=code_dirs,
        )

        self.exp.add_new_file("", self.EXP_RUN_SCRIPT, script, permissions=0o755)

    def start_runs(self):
        tools.run_command(["condor_submit", self.EXP_RUN_SCRIPT], cwd=self.exp.path)

    def run_steps(self, steps):
        if len(steps) > 1:
            logging.warning(
                "Only the run step is executed in Condor, so please execute "
                "manually the build and start steps and when all jobs have "
                "finished in the cluster, then execute the rest of steps"
            )

        for step in steps:
            step()

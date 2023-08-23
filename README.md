# lab-htcondor-environment

This project provides a `HTCondorEnvironment` class to ease the execution of
Lab and Downward Lab in HTCondor clusters.

This project is not available in PyPI yet, so the easiest manners of installing
it are:

- Source your Python virtual environment and then install it with the command
`pip install 'git+https://github.com/Martin1887/lab-htcondor-environment'`.
- Download or clone the repository in a local folder and then install it
executing `pip install <repository_path>` after sourcing your Python virtual
environoment.

The usage is straightforward:

- Import the environment class in your Downward Lab script:
```from lab_htcondor_environment.htcondor_environment import HTCondorEnvironment```
- Create an object of the class like in any other environment:
```env = HTCondorEnvironment()```
The parameters of the constructor are:

  - `nice_user="True"`,
  - `email=""`,
  - `notification_mode="Never"`,
  - `getenv="True"`,
  - `preiority=0`,
  - `uneiverse="vanilla"`,
  - `reequest_memory="0"`,
  - `reequirements_line=""`,
  - `custom_lines=""`.

As `requirements_line` the full requirements line
(including 'requirements = ') can be specified.

As `custom_lines` a string specifying other commands can be inserted.

See :py:class:`~lab.environments.Environment` for inherited
parameters.

Note that email notifications are sent per experiment because each experiment is
created as a different HTCondor job, so enabling notifications may be annoying.

Experiments are executed in the cluster using `condor_submit` and there
is no manner of continue the execution when all experiments have finished.
Therefore, there are two alternatives to launch experiments and reports:

- Write build and run steps in a different Lab script of fetches and reports,
running the last one only when all experiments have finished.
- Write all steps in the same script and run it step by step, running fetches
only when all experiments have finished.


.. _using-command-line-tool:

Using command line tool
=======================

The pip package provides an executable command `watcher-fs`. To run it, use:

.. code-block:: bash

   watcher-fs


You can run the watcher by typing that command into console. It needs a configuration file.
If none is specified, `watcher-fs` looks for `watcher-fs.cfg` in the current working directory.
The config file can be provided by executing:

.. code-block:: bash

   watcher-fs --config <path/to/my_config_file.cfg>

Configuration for watcher-fs
----------------------------

You can register single watcher, where you specify:
   - `"path"` as a glob pattern or a list of exact files to watch
   - `"trigger_type"` - "any_file", "per_file"

      - "any_file" - if any (or multiple) of specified `path` files change, trigger callback once
      - "per_file" - for every files specified by `path`, trigger the callback
   - `"actions"` list of actions to execute when change is detected (callback consist of actions defined here)

      - action can be defined by simple string, i.e. `"notify"`
      - or as a dictionary where you specify params passed to the action, i.e. `"cmd"`

`"notify"` action just outputs a line in the command line describing what happened to what file

`"cmd"` executes command in your console. `cmd` command expects dictionary containing:

   - `"action" : "cmd"`
   - `"cmd": "<command to execute>"` where `{0}` is replaced by the currently modified / created / deleted file. Example: `"cat {0}"`


Example configuration file for watcher-fs
-----------------------------------------

.. code-block:: json

   {
       "path": "test_dir/**",
       "trigger_type": "any_file",
       "actions": [
           "notify",
           {
               "action": "cmd",
               "cmd": "ffprobe {0}"
           },
           {
               "action": "cmd",
               "cmd": "cat {0}"
           },
           "notify"
       ]
   }

You can also specify/register multiple paths/patterns for watcher at once:

.. code-block:: json

   [
      {
         "path": "test_dir/**",
         "trigger_type": "any_file",
         "actions": [ "notify" ]
      },
      {
         "path": "test_dir/**.txt",
         "trigger_type": "per_file",
         "actions": [
            {
               "action": "cmd",
               "cmd": "encode.exe \"{0}\" -o \"../secret/{0}\""
            }
         ]
      }
   ]
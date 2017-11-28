# Profiling tools to generate nvvp traces.

This tools allow to create an nvprof profile or add tasks to an exinsing one.
The timing informations are provided in a CSV file in the following way:
 
Task name, task group, thread id where the task starts, start timestamp (nanoseconds), thread id where the task ends, end timestamp (nanoseconds)

```
usage: python3 prof.py [-h] [--output OUTPUT] [--rank RANK]
                       [--color-dict-filename COLOR_DICT_FILENAME]
                       [--combine-threads COMBINE_THREADS]
                       filename

positional arguments:
  filename              name of the csv profile (input file)

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        The name of the nvprof profile to be created or
                        modified (Default: filename with extension changed to
                        ".nvprof")
  --rank RANK, -r RANK  MPI rank number (default: 0)
  --color-dict-filename COLOR_DICT_FILENAME, -c COLOR_DICT_FILENAME
                        the json file containing the dictionaries
                        "task_colors" and "task_group_colors" (Default:
                        ./task_color.json). If this file doeas not exist a
                        warning message is displayed and the default color is
                        used for all the tasks.
  --combine-threads COMBINE_THREADS, -C COMBINE_THREADS
                        Combine threads in the profile to have a better view
```

Note:
- If the output file exists the tasks are added to the existing file, therefore tasks are added twice if this script is executed twice.
- The MPI ranks has to be specified to allow the "multiple processes" import option of nvvp to open multiple profiles and to display them in the same window.
- The task color is determined in the following order:
  * Match any of the entry of task_colors with the beginning of the task name.
    (E.g. Task "TaskName_1" would match with a possible entry "Task" of the task_colors dictionary) 
  * Match any of the entry of task_group_colors with the beginning of the group name.
  * Default color (nvvp display them in green).

# Example

`example.cpp` can be compiled with a C++14 compiler. An example of output and profiles generated can be found in `example_output`.

The profiles were generated with:

`example_output>>> python3 ../scripts/prof.py output_file.csv`

`example_output>>> python3 ../scripts/prof.py -C 1 -o output_file_combined.nvprof output_file.csv`



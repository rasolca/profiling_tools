# Copyright (c) 2017, Raffaele Solcà
# All rights reserved.
#
# See LICENSE.txt for terms of usage.

import csv
import sys
import nvprof_db
import argparse

parser = argparse.ArgumentParser(description='Insert the data of a csv profile in a nvprof profile')
parser.add_argument('filename', help='name of the csv profile (input file)')
parser.add_argument('--output', '-o', help='The name of the nvprof profile to be created or modified (Default: filename with extension changed to ".nvprof")')
parser.add_argument('--rank', '-r', type=int, default=0, help='MPI rank number (default: 0)')
parser.add_argument('--color-dict-filename', '-c', default="./task_color.json", help='the json file containing the dictionaries "task_colors" and "task_group_colors" (Default: ./task_color.json). If this file doeas not exist a warning message is displayed and the default color is used for all the tasks.')
parser.add_argument('--combine-threads', '-C', type=bool, default=False, help='Combine threads in the profile to have a better view')
args = parser.parse_args()

filename = args.filename
rank_id = args.rank
color_filename = args.color_dict_filename
combined = args.combine_threads
if args.output == None:
  i = filename.rfind('.')
  if i == -1:
    output_filename = filename + '.nvprof'
  else:
    output_filename = filename[:i] + '.nvprof'
else:
  output_filename = args.output

print(filename, rank_id, color_filename, output_filename)

prof_db = nvprof_db.nvprof_db(output_filename, color_filename)

prof_db.insert_process(rank_id)

with open(filename) as csvfile:
  tasks = csv.reader(csvfile, delimiter=',')
  for task in tasks:
    task_name = task[0].strip()
    task_group = task[1].strip()
    tid_st = int(task[2].strip())
    time_st = int(task[3].strip())
    tid_en = int(task[4].strip())
    time_en = int(task[5].strip())
    prof_db.insert_task(rank_id, task_name, task_group, tid_st, time_st, tid_en, time_en, combined=combined)

prof_db.commit()

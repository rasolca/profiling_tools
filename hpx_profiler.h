// Copyright (c) 2017, Raffaele Solcà
// All rights reserved.
//
// See LICENSE.txt for terms of usage.

#ifndef HPX_PROFILER_H
#define HPX_PROFILER_H

#include <chrono>
#include <deque>
#include <string>
#include <vector>
#include <unistd.h>

#include <hpx/hpx.hpp>
#include "hpx/util/annotated_function.hpp"
#include "profiler.h"

namespace profiler {

  class HpxTaskProfiler {
    public:
    HpxTaskProfiler(std::string task_name, std::string task_group_name)
     : task_name_(task_name), task_group_name_(task_group_name), thread_id_start_(getThreadId()),
       time_start_(Profiler::getProfiler().getTime()), apex_profiler(task_name.c_str()) {}

    ~HpxTaskProfiler() {
      int thread_id_end = getThreadId();
      TimeType time_end = Profiler::getProfiler().getTime();

      Profiler::getProfiler().add(task_name_, task_group_name_, thread_id_start_, time_start_,
                                  thread_id_end, time_end);
    }

    int getThreadId() {
      return hpx::get_worker_thread_num();
    }

    private:
    std::string task_name_;
    std::string task_group_name_;
    int thread_id_start_;
    TimeType time_start_;
    hpx::util::annotate_function apex_profiler;
  };
}

#endif  // HPX_PROFILER_H

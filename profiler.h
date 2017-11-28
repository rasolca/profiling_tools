// Copyright (c) 2017, Raffaele Solcà
// All rights reserved.
//
// See LICENSE.txt for terms of usage.

#ifndef PROFILER_H
#define PROFILER_H

#include <chrono>
#include <deque>
#include <string>
#include <vector>
#include <fstream>
#include <unistd.h>
#include "util.h"

namespace profiler {

  using TimeType = unsigned long long;

  class TaskProfileData {
    public:
    TaskProfileData(const std::string& task_name, const std::string& task_group_name,
                    int thread_id_start, TimeType time_start, int thread_id_end, TimeType time_end)
     : task_name_(task_name), task_group_name_(task_group_name), thread_id_start_(thread_id_start),
       time_start_(time_start), thread_id_end_(thread_id_end), time_end_(time_end) {}

    template <class Out>
    void write(Out& out_stream) {
      out_stream << task_name_ << ", ";
      out_stream << task_group_name_ << ", ";
      out_stream << thread_id_start_ << ", ";
      out_stream << time_start_ << ", ";
      out_stream << thread_id_end_ << ", ";
      out_stream << time_end_ << std::endl;
    }

    private:
    std::string task_name_;
    std::string task_group_name_;
    int thread_id_start_;
    TimeType time_start_;
    int thread_id_end_;
    TimeType time_end_;
  };

  class ThreadProfiler {
    public:
    void add(const std::string& task_name, const std::string& task_group_name, int thread_id_start,
             TimeType time_start, int thread_id_end, TimeType time_end) {
      task_profiles.emplace_back(task_name, task_group_name, thread_id_start, time_start,
                                 thread_id_end, time_end);
    }

    template <class Out>
    void write(Out& out_stream) {
      for (auto& task_profile : task_profiles)
        task_profile.write(out_stream);
    }

    private:
    std::deque<TaskProfileData> task_profiles;
  };

  // TODO: Fix interface
  class Profiler {
    public:
    Profiler() : filename_("profile_" + std::to_string(getpid()) + ".txt"), profilers_(257) {}
    ~Profiler() {
      std::ofstream fout(filename_);
      for (auto& profiler : profilers_)
        profiler.write(fout);
    }

    void setOutputFilename(std::string output_name) {
      filename_ = output_name;
    }

    void add(const std::string& task_name, const std::string& task_group_name, int thread_id_start,
             TimeType time_start, int thread_id_end, TimeType time_end) {
      profilers_[thread_id_end + 1].add(task_name, task_group_name, thread_id_start, time_start,
                                        thread_id_end, time_end);
    }

    TimeType getTime() {
      return std::chrono::duration_cast<std::chrono::nanoseconds>(
                 std::chrono::high_resolution_clock::now().time_since_epoch())
          .count();
    }

    static Profiler& getProfiler() {
      static Profiler profiler;
      return profiler;
    }

    private:
    std::string filename_;
    std::vector<ThreadProfiler> profilers_;
  };

  class GenericTaskProfiler {
    public:
    GenericTaskProfiler(int thread_id, std::string task_name, std::string task_group_name)
     : task_name_(task_name), task_group_name_(task_group_name), thread_id_start_(thread_id),
       time_start_(Profiler::getProfiler().getTime()) {}

    ~GenericTaskProfiler() {
      int thread_id_end = thread_id_start_;
      TimeType time_end = Profiler::getProfiler().getTime();

      Profiler::getProfiler().add(task_name_, task_group_name_, thread_id_start_, time_start_,
                                  thread_id_end, time_end);
    }

    private:
    std::string task_name_;
    std::string task_group_name_;
    int thread_id_start_;
    TimeType time_start_;
  };
}

#endif  // PROFILER_H

// Copyright (c) 2017, Raffaele Solcà
// All rights reserved.
//
// See LICENSE.txt for terms of usage.

#include "profiler.h"
#include <iostream>
#include <future>
#include <thread>

void test(int thr_id, std::string name, std::string group) {
  profiler::GenericTaskProfiler tp(thr_id, name, group);
  sleep(1);
}

int main() {
  profiler::Profiler::getProfiler().setOutputFilename("output_file.csv");
  {
    std::vector<std::future<void>> fts;
    for (int i = 0; i < 10; ++i) {
      fts.emplace_back(std::async(test, i, "Task " + std::to_string(i), "Group1"));
    }

    for (auto& ft : fts)
      ft.get();
  }
  {
    std::vector<std::future<void>> fts;
    for (int i = 0; i < 10; ++i) {
      fts.emplace_back(std::async(test, i, "AnotherTask " + std::to_string(i), "Group2"));
    }

    for (auto& ft : fts)
      ft.get();
  }
  {
    std::vector<std::future<void>> fts;
    for (int i = 0; i < 10; ++i) {
      fts.emplace_back(std::async(test, i, "ExtraTask " + std::to_string(i), "Group1"));
    }

    for (auto& ft : fts)
      ft.get();
  }

  return 0;
}

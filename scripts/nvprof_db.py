# Copyright (c) 2017, Raffaele Solcà
# All rights reserved.
#
# See LICENSE.txt for terms of usage.

import sys
import json
import os
import sqlite3

class nvprof_db:

  def __init__(self, filename, color_filename=''):
    if os.path.exists(filename):
      if os.path.isfile(filename):
        self.db = sqlite3.connect(filename)
        dbc = self.db.cursor()
        ids = dbc.execute('SELECT id FROM CUPTI_ACTIVITY_KIND_MARKER').fetchall()
        if len(ids) == 0:
            ids = [(0,)]
        self.task_id = max(ids)[0] + 1
      else:
        print("Database filename {} is a directory".format(filename))
        sys.exit(1)
    else:
      self.db = sqlite3.connect(filename)
      self.create_tables()
      self.task_id = 1
    self.load_color_from_json(color_filename)

  def commit(self):
    self.db.commit()

  def insert_string(self, string):
    dbc = self.db.cursor()
    rows = dbc.execute('SELECT _id_ FROM "StringTable" WHERE value=?', (string,)).fetchall()
    if len(rows) > 0:
      return rows[0][0]
    dbc.execute('INSERT INTO "StringTable" (value) VALUES' + "(?)", (string,));
    return dbc.lastrowid

  def insert_process(self, rank_id):
    dbc = self.db.cursor()
    id_str_rank = self.insert_string("Rank")
    dbc.execute('INSERT INTO "CUPTI_ACTIVITY_KIND_NAME" (objectKind, objectId, name) VALUES(1,?,?)', (hex_ProcThreadId(rank_id, 0), id_str_rank))

  def insert_task(self, id_rank, task_name, task_group, tid_st, time_st, tid_end, time_end, combined=False):
    str_id = self.insert_string(task_name)
    if combined and tid_st >= 0:
      task_group_id = self.insert_string("Thread {}".format(tid_st))
      tid_st = 0
      tid_end = 0
    else:
      task_group_id = self.insert_string(task_group)
    task_id_ = self.task_id
    self.task_id += 1
    self.insert_task_entry(time_st, 2, task_id_, hex_ProcThreadId(id_rank, tid_st), str_id, task_group_id)
    self.insert_task_entry(time_end, 4, task_id_, hex_ProcThreadId(id_rank, tid_end), 0, 0)
    self.task_color(task_id_, task_name, task_group)

  def insert_task_entry(self, time_st, entry_kind_id, task_id, tid_st, str_id, task_group_id):
    dbc = self.db.cursor()
    dbc.execute('INSERT INTO "CUPTI_ACTIVITY_KIND_MARKER" (flags, timestamp, id, objectKind, objectId, name, domain) VALUES(?,?,?,2,?,?,?)', (entry_kind_id, time_st, task_id, tid_st, str_id, task_group_id))

  def task_color(self, task_id, task_name, task_group):
    for task in self.task_colors:
      if task_name[0:len(task)] == task:
        self.insert_task_color(task_id, self.task_colors[task])
        return
    for group in self.task_group_colors:
      if task_group[0:len(group)] == group:
        self.insert_task_color(task_id, self.task_group_colors[group])
        return
    #if task_name in self.task_colors:
    #  self.insert_task_color(task_id, self.task_colors[task_name])
    #elif task_group in self.task_group_colors:
    #  self.insert_task_color(task_id, self.task_group_colors[task_group])

  def insert_task_color(self, task_id, color):
    dbc = self.db.cursor()
    dbc.execute('INSERT INTO "CUPTI_ACTIVITY_KIND_MARKER_DATA" (flags, id, payloadKind, payload, color, category) VALUES(2,?,1,?,?,0);', (task_id, sqlite3.Binary(b'\x00'*8), color_id(color)))

  def load_color_from_json(self, filename=''):
    self.task_colors = {}
    self.task_group_colors = {}
    if filename == '':
      filename = 'task_colors.json'
    if not os.path.isfile(filename):
      print("Warning: {} not found.".format(filename), file=sys.stderr)
      return

    with open(filename) as data_file:
      data = json.load(data_file)
      if "task_colors" in data:
        self.task_colors = data["task_colors"]
      else:
        print("Warning: {} do not contain task_color dictionary.".format(filename), file=sys.stderr)
      if "task_group_colors" in data:
        self.task_group_colors = data["task_group_colors"]
      else:
        print("Warning: {} do not contain task_group_color dictionary.".format(filename), file=sys.stderr)

  def create_tables(self):
    dbc = self.db.cursor()
    dbc.execute('CREATE TABLE StringTable( _id_ INTEGER PRIMARY KEY AUTOINCREMENT, value TEXT NOT NULL UNIQUE )')
    dbc.execute('CREATE TABLE Version( version INTEGER)')
    dbc.execute('INSERT INTO "Version" VALUES(9)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_MEMCPY(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, copyKind INT NOT NULL, srcKind INT NOT NULL, dstKind INT NOT NULL, flags INT NOT NULL, bytes INT NOT NULL, start INT NOT NULL, end INT NOT NULL, deviceId INT NOT NULL, contextId INT NOT NULL, streamId INT NOT NULL, correlationId INT NOT NULL, runtimeCorrelationId INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_MEMSET(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, value INT NOT NULL, bytes INT NOT NULL, start INT NOT NULL, end INT NOT NULL, deviceId INT NOT NULL, contextId INT NOT NULL, streamId INT NOT NULL, correlationId INT NOT NULL, flags INT NOT NULL, memoryKind INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_KERNEL(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, cacheConfig BLOB NOT NULL, sharedMemoryConfig INT NOT NULL, registersPerThread INT NOT NULL, partitionedGlobalCacheRequested INT NOT NULL, partitionedGlobalCacheExecuted INT NOT NULL, start INT NOT NULL, end INT NOT NULL, completed INT NOT NULL, deviceId INT NOT NULL, contextId INT NOT NULL, streamId INT NOT NULL, gridX INT NOT NULL, gridY INT NOT NULL, gridZ INT NOT NULL, blockX INT NOT NULL, blockY INT NOT NULL, blockZ INT NOT NULL, staticSharedMemory INT NOT NULL, dynamicSharedMemory INT NOT NULL, localMemoryPerThread INT NOT NULL, localMemoryTotal INT NOT NULL, correlationId INT NOT NULL, gridId INT NOT NULL, name INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_DRIVER(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, cbid INT NOT NULL, start INT NOT NULL, end INT NOT NULL, processId INT NOT NULL, threadId INT NOT NULL, correlationId INT NOT NULL, returnValue INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_RUNTIME(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, cbid INT NOT NULL, start INT NOT NULL, end INT NOT NULL, processId INT NOT NULL, threadId INT NOT NULL, correlationId INT NOT NULL, returnValue INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_EVENT(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, id INT NOT NULL, value INT NOT NULL, domain INT NOT NULL, correlationId INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_METRIC(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, id INT NOT NULL, value BLOB NOT NULL, correlationId INT NOT NULL, flags INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_DEVICE(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, flags INT NOT NULL, globalMemoryBandwidth INT NOT NULL, globalMemorySize INT NOT NULL, constantMemorySize INT NOT NULL, l2CacheSize INT NOT NULL, numThreadsPerWarp INT NOT NULL, coreClockRate INT NOT NULL, numMemcpyEngines INT NOT NULL, numMultiprocessors INT NOT NULL, maxIPC INT NOT NULL, maxWarpsPerMultiprocessor INT NOT NULL, maxBlocksPerMultiprocessor INT NOT NULL, maxSharedMemoryPerMultiprocessor INT NOT NULL, maxRegistersPerMultiprocessor INT NOT NULL, maxRegistersPerBlock INT NOT NULL, maxSharedMemoryPerBlock INT NOT NULL, maxThreadsPerBlock INT NOT NULL, maxBlockDimX INT NOT NULL, maxBlockDimY INT NOT NULL, maxBlockDimZ INT NOT NULL, maxGridDimX INT NOT NULL, maxGridDimY INT NOT NULL, maxGridDimZ INT NOT NULL, computeCapabilityMajor INT NOT NULL, computeCapabilityMinor INT NOT NULL, id INT NOT NULL, eccEnabled INT NOT NULL, uuid BLOB NOT NULL, name INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_CONTEXT(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, contextId INT NOT NULL, deviceId INT NOT NULL, computeApiKind INT NOT NULL, nullStreamId INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, cacheConfig BLOB NOT NULL, sharedMemoryConfig INT NOT NULL, registersPerThread INT NOT NULL, partitionedGlobalCacheRequested INT NOT NULL, partitionedGlobalCacheExecuted INT NOT NULL, start INT NOT NULL, end INT NOT NULL, completed INT NOT NULL, deviceId INT NOT NULL, contextId INT NOT NULL, streamId INT NOT NULL, gridX INT NOT NULL, gridY INT NOT NULL, gridZ INT NOT NULL, blockX INT NOT NULL, blockY INT NOT NULL, blockZ INT NOT NULL, staticSharedMemory INT NOT NULL, dynamicSharedMemory INT NOT NULL, localMemoryPerThread INT NOT NULL, localMemoryTotal INT NOT NULL, correlationId INT NOT NULL, gridId INT NOT NULL, name INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_NAME(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, objectKind INT NOT NULL, objectId BLOB NOT NULL, name INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_MARKER(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, flags INT NOT NULL, timestamp INT NOT NULL, id INT NOT NULL, objectKind INT NOT NULL, objectId BLOB NOT NULL, name INT NOT NULL, domain INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_MARKER_DATA(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, flags INT NOT NULL, id INT NOT NULL, payloadKind INT NOT NULL, payload BLOB NOT NULL, color INT NOT NULL, category INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_SOURCE_LOCATOR(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, id INT NOT NULL, lineNumber INT NOT NULL, fileName INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_GLOBAL_ACCESS(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, flags INT NOT NULL, sourceLocatorId INT NOT NULL, correlationId INT NOT NULL, functionId INT NOT NULL, pcOffset INT NOT NULL, threadsExecuted INT NOT NULL, l2_transactions INT NOT NULL, theoreticalL2Transactions INT NOT NULL, executed INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_BRANCH(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, sourceLocatorId INT NOT NULL, correlationId INT NOT NULL, functionId INT NOT NULL, pcOffset INT NOT NULL, diverged INT NOT NULL, threadsExecuted INT NOT NULL, executed INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_OVERHEAD(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, overheadKind INT NOT NULL, objectKind INT NOT NULL, objectId BLOB NOT NULL, start INT NOT NULL, end INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_CDP_KERNEL(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, cacheConfig BLOB NOT NULL, sharedMemoryConfig INT NOT NULL, registersPerThread INT NOT NULL, start INT NOT NULL, end INT NOT NULL, deviceId INT NOT NULL, contextId INT NOT NULL, streamId INT NOT NULL, gridX INT NOT NULL, gridY INT NOT NULL, gridZ INT NOT NULL, blockX INT NOT NULL, blockY INT NOT NULL, blockZ INT NOT NULL, staticSharedMemory INT NOT NULL, dynamicSharedMemory INT NOT NULL, localMemoryPerThread INT NOT NULL, localMemoryTotal INT NOT NULL, correlationId INT NOT NULL, gridId INT NOT NULL, parentGridId INT NOT NULL, queued INT NOT NULL, submitted INT NOT NULL, completed INT NOT NULL, parentBlockX INT NOT NULL, parentBlockY INT NOT NULL, parentBlockZ INT NOT NULL, name INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_PREEMPTION(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, preemptionKind INT NOT NULL, timestamp INT NOT NULL, gridId INT NOT NULL, blockX INT NOT NULL, blockY INT NOT NULL, blockZ INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_ENVIRONMENT(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, deviceId INT NOT NULL, timestamp INT NOT NULL, environmentKind INT NOT NULL, data BLOB NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_EVENT_INSTANCE(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, id INT NOT NULL, domain INT NOT NULL, instance INT NOT NULL, value INT NOT NULL, correlationId INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_MEMCPY2(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, copyKind INT NOT NULL, srcKind INT NOT NULL, dstKind INT NOT NULL, flags INT NOT NULL, bytes INT NOT NULL, start INT NOT NULL, end INT NOT NULL, deviceId INT NOT NULL, contextId INT NOT NULL, streamId INT NOT NULL, srcDeviceId INT NOT NULL, srcContextId INT NOT NULL, dstDeviceId INT NOT NULL, dstContextId INT NOT NULL, correlationId INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_METRIC_INSTANCE(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, id INT NOT NULL, value BLOB NOT NULL, instance INT NOT NULL, correlationId INT NOT NULL, flags INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_INSTRUCTION_EXECUTION(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, flags INT NOT NULL, sourceLocatorId INT NOT NULL, correlationId INT NOT NULL, functionId INT NOT NULL, pcOffset INT NOT NULL, threadsExecuted INT NOT NULL, notPredOffThreadsExecuted INT NOT NULL, executed INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_UNIFIED_MEMORY_COUNTER(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, counterKind INT NOT NULL, value INT NOT NULL, start INT NOT NULL, end INT NOT NULL, address INT NOT NULL, srcId INT NOT NULL, dstId INT NOT NULL, streamId INT NOT NULL, processId INT NOT NULL, flags INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_FUNCTION(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, id INT NOT NULL, contextId INT NOT NULL, moduleId INT NOT NULL, functionIndex INT NOT NULL, name INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_MODULE(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, contextId INT NOT NULL, id INT NOT NULL, cubinSize INT NOT NULL, cubin BLOB NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_DEVICE_ATTRIBUTE(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, flags INT NOT NULL, deviceId INT NOT NULL, attribute BLOB NOT NULL, value BLOB NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_SHARED_ACCESS(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, flags INT NOT NULL, sourceLocatorId INT NOT NULL, correlationId INT NOT NULL, functionId INT NOT NULL, pcOffset INT NOT NULL, threadsExecuted INT NOT NULL, sharedTransactions INT NOT NULL, theoreticalSharedTransactions INT NOT NULL, executed INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_PC_SAMPLING(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, flags INT NOT NULL, sourceLocatorId INT NOT NULL, correlationId INT NOT NULL, functionId INT NOT NULL, pcOffset INT NOT NULL, latencySamples INT NOT NULL, samples INT NOT NULL, stallReason INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_PC_SAMPLING_RECORD_INFO(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, correlationId INT NOT NULL, totalSamples INT NOT NULL, droppedSamples INT NOT NULL, samplingPeriodInCycles INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_INSTRUCTION_CORRELATION(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, flags INT NOT NULL, sourceLocatorId INT NOT NULL, functionId INT NOT NULL, pcOffset INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_OPENACC_DATA(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, eventKind INT NOT NULL, parentConstruct INT NOT NULL, version INT NOT NULL, implicit INT NOT NULL, deviceType INT NOT NULL, deviceNumber INT NOT NULL, threadId INT NOT NULL, async INT NOT NULL, asyncMap INT NOT NULL, lineNo INT NOT NULL, endLineNo INT NOT NULL, funcLineNo INT NOT NULL, funcEndLineNo INT NOT NULL, start INT NOT NULL, end INT NOT NULL, cuDeviceId INT NOT NULL, cuContextId INT NOT NULL, cuStreamId INT NOT NULL, cuProcessId INT NOT NULL, cuThreadId INT NOT NULL, externalId INT NOT NULL, srcFile INT NOT NULL, funcName INT NOT NULL, bytes INT NOT NULL, hostPtr INT NOT NULL, devicePtr INT NOT NULL, varName INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_OPENACC_LAUNCH(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, eventKind INT NOT NULL, parentConstruct INT NOT NULL, version INT NOT NULL, implicit INT NOT NULL, deviceType INT NOT NULL, deviceNumber INT NOT NULL, threadId INT NOT NULL, async INT NOT NULL, asyncMap INT NOT NULL, lineNo INT NOT NULL, endLineNo INT NOT NULL, funcLineNo INT NOT NULL, funcEndLineNo INT NOT NULL, start INT NOT NULL, end INT NOT NULL, cuDeviceId INT NOT NULL, cuContextId INT NOT NULL, cuStreamId INT NOT NULL, cuProcessId INT NOT NULL, cuThreadId INT NOT NULL, externalId INT NOT NULL, srcFile INT NOT NULL, funcName INT NOT NULL, numGangs INT NOT NULL, numWorkers INT NOT NULL, vectorLength INT NOT NULL, kernelName INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_OPENACC_OTHER(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, eventKind INT NOT NULL, parentConstruct INT NOT NULL, version INT NOT NULL, implicit INT NOT NULL, deviceType INT NOT NULL, deviceNumber INT NOT NULL, threadId INT NOT NULL, async INT NOT NULL, asyncMap INT NOT NULL, lineNo INT NOT NULL, endLineNo INT NOT NULL, funcLineNo INT NOT NULL, funcEndLineNo INT NOT NULL, start INT NOT NULL, end INT NOT NULL, cuDeviceId INT NOT NULL, cuContextId INT NOT NULL, cuStreamId INT NOT NULL, cuProcessId INT NOT NULL, cuThreadId INT NOT NULL, externalId INT NOT NULL, srcFile INT NOT NULL, funcName INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_CUDA_EVENT(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, correlationId INT NOT NULL, contextId INT NOT NULL, streamId INT NOT NULL, eventId INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_STREAM(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, contextId INT NOT NULL, streamId INT NOT NULL, priority INT NOT NULL, flag INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, type INT NOT NULL, start INT NOT NULL, end INT NOT NULL, correlationId INT NOT NULL, contextId INT NOT NULL, streamId INT NOT NULL, cudaEventId INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_EXTERNAL_CORRELATION(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, externalKind INT NOT NULL, externalId INT NOT NULL, correlationId INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_NVLINK(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, nvlinkVersion INT NOT NULL, typeDev0 INT NOT NULL, typeDev1 INT NOT NULL, idDev0 BLOB NOT NULL, idDev1 BLOB NOT NULL, flag INT NOT NULL, physicalNvLinkCount INT NOT NULL, portDev0 BLOB NOT NULL, portDev1 BLOB NOT NULL, bandwidth INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_INSTANTANEOUS_EVENT(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, id INT NOT NULL, value INT NOT NULL, timestamp INT NOT NULL, deviceId INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_INSTANTANEOUS_EVENT_INSTANCE(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, id INT NOT NULL, value INT NOT NULL, timestamp INT NOT NULL, deviceId INT NOT NULL, instance INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_INSTANTANEOUS_METRIC(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, id INT NOT NULL, value BLOB NOT NULL, timestamp INT NOT NULL, deviceId INT NOT NULL, flags INT NOT NULL)')
    dbc.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_INSTANTANEOUS_METRIC_INSTANCE(_id_ INTEGER PRIMARY KEY AUTOINCREMENT, id INT NOT NULL, value BLOB NOT NULL, timestamp INT NOT NULL, deviceId INT NOT NULL, flags INT NOT NULL, instance INT NOT NULL)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_MEMCPY ON CUPTI_ACTIVITY_KIND_MEMCPY(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_MEMSET ON CUPTI_ACTIVITY_KIND_MEMSET(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_KERNEL ON CUPTI_ACTIVITY_KIND_KERNEL(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_DRIVER ON CUPTI_ACTIVITY_KIND_DRIVER(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_RUNTIME ON CUPTI_ACTIVITY_KIND_RUNTIME(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_EVENT ON CUPTI_ACTIVITY_KIND_EVENT(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_METRIC ON CUPTI_ACTIVITY_KIND_METRIC(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL ON CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_MARKER ON CUPTI_ACTIVITY_KIND_MARKER(timestamp)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_GLOBAL_ACCESS ON CUPTI_ACTIVITY_KIND_GLOBAL_ACCESS(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_BRANCH ON CUPTI_ACTIVITY_KIND_BRANCH(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_OVERHEAD ON CUPTI_ACTIVITY_KIND_OVERHEAD(start)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_CDP_KERNEL ON CUPTI_ACTIVITY_KIND_CDP_KERNEL(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_PREEMPTION ON CUPTI_ACTIVITY_KIND_PREEMPTION(timestamp)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_ENVIRONMENT ON CUPTI_ACTIVITY_KIND_ENVIRONMENT(timestamp)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_EVENT_INSTANCE ON CUPTI_ACTIVITY_KIND_EVENT_INSTANCE(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_MEMCPY2 ON CUPTI_ACTIVITY_KIND_MEMCPY2(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_METRIC_INSTANCE ON CUPTI_ACTIVITY_KIND_METRIC_INSTANCE(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_INSTRUCTION_EXECUTION ON CUPTI_ACTIVITY_KIND_INSTRUCTION_EXECUTION(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_UNIFIED_MEMORY_COUNTER ON CUPTI_ACTIVITY_KIND_UNIFIED_MEMORY_COUNTER(start)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_SHARED_ACCESS ON CUPTI_ACTIVITY_KIND_SHARED_ACCESS(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_PC_SAMPLING ON CUPTI_ACTIVITY_KIND_PC_SAMPLING(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_PC_SAMPLING_RECORD_INFO ON CUPTI_ACTIVITY_KIND_PC_SAMPLING_RECORD_INFO(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_OPENACC_DATA ON CUPTI_ACTIVITY_KIND_OPENACC_DATA(start)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_OPENACC_LAUNCH ON CUPTI_ACTIVITY_KIND_OPENACC_LAUNCH(start)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_OPENACC_OTHER ON CUPTI_ACTIVITY_KIND_OPENACC_OTHER(start)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_CUDA_EVENT ON CUPTI_ACTIVITY_KIND_CUDA_EVENT(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_SYNCHRONIZATION ON CUPTI_ACTIVITY_KIND_SYNCHRONIZATION(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_EXTERNAL_CORRELATION ON CUPTI_ACTIVITY_KIND_EXTERNAL_CORRELATION(correlationId)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_INSTANTANEOUS_EVENT ON CUPTI_ACTIVITY_KIND_INSTANTANEOUS_EVENT(timestamp)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_INSTANTANEOUS_EVENT_INSTANCE ON CUPTI_ACTIVITY_KIND_INSTANTANEOUS_EVENT_INSTANCE(timestamp)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_INSTANTANEOUS_METRIC ON CUPTI_ACTIVITY_KIND_INSTANTANEOUS_METRIC(timestamp)')
    dbc.execute('CREATE INDEX INDEX_CUPTI_ACTIVITY_KIND_INSTANTANEOUS_METRIC_INSTANCE ON CUPTI_ACTIVITY_KIND_INSTANTANEOUS_METRIC_INSTANCE(timestamp)')


def hex_ProcThreadId(pid, tid):
  signed = False
  if tid < 0:
    signed = True
  s = pid.to_bytes(4, byteorder='little') + tid.to_bytes(8, byteorder='little', signed=signed)
  return sqlite3.Binary(s)

def color_id(color):
  return int('0xFF'+color, 16)

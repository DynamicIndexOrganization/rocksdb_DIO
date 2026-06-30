# DIO: Dynamic Memtable Index Organization
Dynamic Memtable Index Organization (DIO) is a cost-driven framework that dynamically adapts the memtable type according to workload characteristics. DIO models query costs by dissecting queries into primitive memory operations, predicts the workload cost under multiple memtable types, and selects a memtable that minimizes cost. DIO performs memtable (type) transitions at meaningful memtable lifecycle boundaries, enabling efficient adaptation with minimal disruption to system execution. DIO incorporates mechanisms for early detection of workload shifts and on-the-fly memtable conversion, enabling the system to rapidly converge on the most suitable memtable type after workload changes.

This repository contains DIO prototype implemented on top of RocksDB (version 10.0.0).

## Compilation
To compile this repository, you need to first follow the guidelines of RocksDB compilation [here](https://github.com/facebook/rocksdb/blob/main/INSTALL.md), which lists out the major dependencies and libraries required for compilation. DIO can be compiled in two ways: normal execution and a special latency collection mode. The normal execution compilation will be the same as the RocksDB compilation, and it should be used for benchmarking. The latency collection mode is used to collect latency data to train a linear model used by DIO cost models during cost prediction.

### Environment Variables
To run and compile DIO, you need to define the following two environment variables:
```
// Directory stores the learned linear model used by the DIO cost model
export LATENCY_PREDICT_MODEL_PATH=<PATH-TO-DIO-MODEL>
// Directory stores the collected latency data when enabling latency collection mode
export LATENCY_SAMPLE_STORAGE_PATH=<PATH-TO-DIO-LATENCY>
```

### Normal Execution Mode
To run and compile DIO in the normal execution mode, you need either of the following commands:
```
// To clean up object files and Java target files
make -sj12 clean jclean

// To compile DIO in debug mode with -O0 optimization
make -sj12

// To compile DIO in release mode with -O2 optimization
make -sj12 release

// To compile DIO into a Java library and generate related files
//    This command will be used for benchmarking in YCSB_DIO
make -sj12 rocksdbjavastatic
```

### Latency collection mode
To enable the latency collection framework of primative operations, use the following command:
```
make -sj12 dio_sample
```
This build option will define the flag DIO_LATENCY_COLLECT during compilation and enable any code block that is surrounded by:
```
#ifdef DIO_LATENCY_COLLECT
...
#endif
```
Such code blocks are disabled in the Normal Execution Mode.


## Latency Model Training
To run DIO properly, you need to train latency models of primative operations on your hardware first. Here is the detailed steps to get you prepared.

1. Compile DIO using Latency collection mode
2. Create both LATENCY_PREDICT_MODEL_PATH and LATENCY_SAMPLE_STORAGE_PATH in the desired location (could be just the current directory)
3. Run the following command to collect latency data for <code>Vector</code>, <code>SkipList</code>, and <code>HashSkipList</code> memtables. We use <code>readrandomwriterandom</code> workload of <code>db_bench</code> to collect such samples. These commands will run it for 60 seconds.
```
# Before running, make sure you replace <path_to_data> with the desired location (NVME SSD recommended for better performance)
# We use the following configurations:
#  1. 1 GB memtable size
#  2. 4 concurrent threads
#  3. WAL is disabled
#  4. 4 max background compaction/flush jobs
#  5. allow_concurrent_memtable_write set to false
#  6. disable_auto_compactions is disabled
#  7. async_io is enabled
#  8. The percentage of read-write is 50-50
#  9. The prefix_size for HashSkipList is set to 8
# You can change these parameters if you want to match your designed workload. They are set to measure the pure performance of memtable operations.

# For Vector Memtable
rm -rf <path_to_data>;./db_bench --benchmarks="readrandomwriterandom" --threads=4 --db=<path_to_data> --memtablerep=vector -write_buffer_size=1073741824 -disable_wal -max_background_jobs=4 --allow_concurrent_memtable_write=false --disable_auto_compactions=1 -async_io -duration=60 -readwritepercent=50 -prefix_size=8
# For SkipList Memtable
rm -rf <path_to_data>;./db_bench --benchmarks="readrandomwriterandom" --threads=4 --db=<path_to_data> --memtablerep=skip_list -write_buffer_size=1073741824 -disable_wal -max_background_jobs=4 --allow_concurrent_memtable_write=false --disable_auto_compactions=1 -async_io -duration=60 -readwritepercent=50 -prefix_size=8
# For HashSkipList Memtable
rm -rf <path_to_data>;./db_bench --benchmarks="readrandomwriterandom" --threads=4 --db=<path_to_data> --memtablerep=prefix_hash -write_buffer_size=1073741824 -disable_wal -max_background_jobs=4 -max_write_buffer_number=4 --allow_concurrent_memtable_write=false --disable_auto_compactions=1 -async_io -duration=60 -readwritepercent=50 -prefix_size=8
```
After running these tests, you should find the following files in <code> LATENCY_SAMPLE_STORAGE_PATH </code>:
```
curOpLatencyCollect_Hash_Probe.csv
curOpLatencyCollect_Inline_Skiplist_Insert.csv
curOpLatencyCollect_Inline_Skiplist_Search.csv
curOpLatencyCollect_Skiplist_Insert.csv
curOpLatencyCollect_Skiplist_Search.csv
curOpLatencyCollect_Vector_Copy.csv
curOpLatencyCollect_Vector_Insert.csv
curOpLatencyCollect_Vector_Sort.csv
```
  Each saves collected latency data for one primative operation. The reason we have both <code>Inline_SkipList_XXXXXX</code> and <code>SkipList_XXXXXX</code> is that SkipList uses <code>class InlineSkipList</code> as its internal data structure while HashSkipList uses <code>class SkipList</code>. For the implementation of <code>Vector</code>, <code>SkipList</code>, and <code>HashSkipList</code>, we keep the original design from RocksDB without optimization, to isolate the effect of DIO.

4. After the latency data are collected, go to each sub-directory within the <code>training</code> directory to run the Python training scripts for each primitive operation.
```
python train.py
```
It will read the collected latency sample, train a pre-set linear model on the sampled data, and save the model parameters to the directory <code>LATENCY_PREDICT_MODEL_PATH</code>. The training script also displays the fitted curve, allowing for further adjustment of the selected model. To use a different model, please update the function <code>model_function</code>

## Running Benchmark
To run our dynamic workload Benchmark, please refer to the README of [YCSB-DIO](https://github.com/DynamicIndexOrganization/YCSB_DIO). Here, you need to compile DIO into java library using the following command:
```
make -sj12 rocksdbjavastatic
```

## Original README of RocksDB

RocksDB is developed and maintained by Facebook Database Engineering Team.
It is built on earlier work on [LevelDB](https://github.com/google/leveldb) by Sanjay Ghemawat (sanjay@google.com)
and Jeff Dean (jeff@google.com)

This code is a library that forms the core building block for a fast
key-value server, especially suited for storing data on flash drives.
It has a Log-Structured-Merge-Database (LSM) design with flexible tradeoffs
between Write-Amplification-Factor (WAF), Read-Amplification-Factor (RAF)
and Space-Amplification-Factor (SAF). It has multi-threaded compactions,
making it especially suitable for storing multiple terabytes of data in a
single database.

Start with example usage here: https://github.com/facebook/rocksdb/tree/main/examples

See the [github wiki](https://github.com/facebook/rocksdb/wiki) for more explanation.

The public interface is in `include/`.  Callers should not include or
rely on the details of any other header files in this package.  Those
internal APIs may be changed without warning.

Questions and discussions are welcome on the [RocksDB Developers Public](https://www.facebook.com/groups/rocksdb.dev/) Facebook group and [email list](https://groups.google.com/g/rocksdb) on Google Groups.

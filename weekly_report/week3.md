# 周报（2026-09-28 至 2026-10-04）

## 本周进展

本周重点从仿真框架继续推进到真实工具链的本地准备，主要完成了 QLLVM 编译器环境的适配、MPI/MPI-Q 通信环境的检查，以及 QOS 对真实工具链的调用入口整理。

### 1. 排查 QLLVM 的 LLVM/MLIR 版本依赖

- 尝试使用 Debian 12 系统中的 LLVM 19 和 LLVM 14 配置 QLLVM。
- 发现 QLLVM 源码依赖旧版 MLIR target，包括 `MLIRTargetLLVMIR` 和 `MLIRStandard`。
- 确认 LLVM 19、LLVM 14 的 target 命名已经发生变化，因此不能简单通过设置 `MLIR_DIR` 解决。
- 结合 QLLVM 官方安装文档，确认其推荐使用 LLVM 12.0.0 预编译工具链。

### 2. 通过镜像完成 LLVM 12 用户目录安装

- 由于 GitHub 直接下载不稳定，改用可访问的镜像下载 LLVM 12 预编译包。
- 将 LLVM 12 安装到用户目录：`$HOME/.llvm`，不需要修改系统目录，也不需要管理员权限。
- 验证 LLVM 12 中包含 QLLVM需要的 `MLIRStandard` 和 `MLIRTargetLLVMIR`。
- 配置了 QLLVM 和 LLVM 的 PATH、LD_LIBRARY_PATH 环境变量。

### 3. 成功编译并安装 QLLVM

- 使用 LLVM 12重新配置 QLLVM：

  ```bash
  cmake -S . -B build -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DLLVM_ROOT="$HOME/.llvm" \
    -DMLIR_DIR="$HOME/.llvm/lib/cmake/mlir"
  ```

- 解决了 QLLVM 源码在当前 GCC 环境下缺少 `<optional>` 头文件的问题，采用 CMake 编译参数 `-DCMAKE_CXX_FLAGS='-include optional'`，没有修改 QLLVM 源码。
- 完成 QLLVM 编译和用户目录安装，安装位置为 `$HOME/.qllvm`。
- 验证 `qllvm` 和 `qllvm-compile` 命令可以正常启动。
- 使用 QLLVM 驱动成功生成了 Bell QASM 编译产物，说明本地编译链已经可以工作。

### 4. 完成 MPI/MPI-Q 本地接入准备

- 确认系统中的 `mpirun` 和 MPI C/C++运行环境可以被 QLLVM检测到。
- QOS中已经增加 MPI-Q 通信适配入口，可以通过配置的 MPI-Q runner 调用真实通信程序。
- 明确 MPI-Q仓库本身主要提供 C/MPI 通信库和示例程序，还需要结合实验室量子控制卡或服务端程序编写一个真正的 runner。
- 当前配置支持通过 `{program}`、`{job_id}` 和 `{shots}`向 MPI-Q runner 传递编译产物和任务参数。

### 5. QOS真实工具链适配结构

- 编译层通过 QLLVM 适配器调用真实 `qllvm` 命令。
- 通信层通过 MPI-Q 适配器调用配置的 `mpirun` 程序。
- 执行层预留 Fusion Lab HTTP提交适配器，可以传输编译后的 QASM、后端名称和 shots参数。
- 通过 `runtime.mode` 区分模拟模式和真实模式，默认模拟实验仍然可以独立运行。
- 新增真实工具链配置模板和环境检查脚本，便于后续部署到实验室环境。

## 验证结果

- QLLVM使用 LLVM 12配置成功。
- QLLVM完成编译和安装。
- `qllvm --help` 可以正常运行。
- MPI运行环境已被检测到。
- QOS原有回归测试保持通过。
- 当前环境检查结果只剩 Fusion Lab真实 API尚未配置。

## 当前问题

目前还不能完成真实量子硬件端到端运行，原因是：

1. Fusion Lab登录平台没有公开可直接使用的提交 API 文档。
2. 尚未获得 Fusion Lab 的认证方式、任务提交接口、任务状态查询接口和结果返回格式。
3. MPI-Q仓库没有一个可以直接接收本项目 QASM任务的通用 runner，需要结合实验室实际控制设备进一步开发。

## 下周计划

### 1. 完成 MPI-Q runner

- 根据 MPI-Q接口和实验室量子控制设备，确定 QASM到脉冲/控制指令的转换方式。
- 编写一个最小 runner，能够接收 QASM文件、shots和任务 ID，并通过 MPI-Q完成一次真实通信。
- 使用 MPI-Q自带的 server 和 test程序先完成局域网内通信验证。

### 2. 获取 Fusion Lab接口信息

- 向老师或平台管理员索取 API/SDK文档。
- 明确提交、轮询、取消任务和获取测量结果的接口。
- 确认认证方式和可用 backend 名称。

### 3. 完成真实 QOS链路验证

- 使用 Bell 态程序完成 QLLVM编译、MPI-Q准备和 Fusion Lab提交的完整流程。
- 将真实排队时间、编译耗时、执行耗时、失败状态和测量结果写回 QOS实验结果。
- 对比当前模拟结果和真实运行结果之间的差异。

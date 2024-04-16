// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

// System regs
localparam [31:0] ID_VERSION_REG = 32'h0000_0000; // ro
localparam [31:0] CAPABILITY_REG = 32'h0000_0004; // ro

// User regs (rw)
localparam [31:0] USER_0_REG = 32'h0000_0008;
localparam [31:0] USER_1_BASE = 32'h0000_0040;
localparam [31:0] PER_USER_OFFSET = 32'h0000_0010;

// Per-queue regs
localparam [31:0] ENABLE_REG = 32'h0000_0100; // rw
localparam [31:0] RESET_REG = 32'h0000_0104; // rw
localparam [31:0] STATUS_REG = 32'h0000_0108; // ro
localparam [31:0] BASE_ADDR_LO_REG = 32'h0000_010c; // rw
localparam [31:0] BASE_ADDR_HI_REG = 32'h0000_0110; // rw
localparam [31:0] CAPACITY_REG = 32'h0000_0114; // rw

localparam REG_OFFSET = 32'h100;

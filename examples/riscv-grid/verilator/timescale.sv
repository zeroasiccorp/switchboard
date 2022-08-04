// needed to prevent a verilator error about timescale not being set
// in a backwards-compatible manner.  the problem is that older versions
// of verilator do not complain, but also do not have options to
// override or disable timescale warnings.  newer versions require
// these features to disable an error, so the simple solution
// is just to include a file at the very beginning of the source
// list that contains the timescale.

`timescale 1ns/1ps
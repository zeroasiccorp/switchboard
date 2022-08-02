module perf_meas_sim #(
    parameter integer default_cycles_per_meas=1000
) (
    input clk
);
    // internal signals
    real t;
    real sim_rate;
    integer cycles_per_meas=default_cycles_per_meas;
    integer total_clock_cycles=0;

    `ifdef __ICARUS__
        task pi_time_taken(output real t);
            $pi_time_taken(t);
        endtask
        task init(input integer n);
            cycles_per_meas = n;
            pi_time_taken(t); //
        endtask
    `else
        import "DPI-C" function void pi_time_taken(output real t);
    `endif

    function void init(input integer n);
        cycles_per_meas = n;
    endfunction

	initial begin
		/* verilator lint_off IGNOREDRETURN */
		pi_time_taken(t);  // discard first result since it is invalid
		/* verilator lint_on IGNOREDRETURN */
	end

	always @(posedge clk) begin
		if (total_clock_cycles >= cycles_per_meas) begin
			/* verilator lint_off IGNOREDRETURN */
			pi_time_taken(t);
			/* verilator lint_on IGNOREDRETURN */
			sim_rate = (1.0*total_clock_cycles)/t;
			if (sim_rate < 1.0e6) begin
				$display("Simulation rate: %0.3f kHz", 1e-3*sim_rate);
			end else begin
				$display("Simulation rate: %0.3f MHz", 1e-6*sim_rate);
			end
			total_clock_cycles <= 0;
		end else begin
			total_clock_cycles <= total_clock_cycles + 1;
		end
	end

endmodule

`timescale 1ns / 1ps

module guardian_fpga (
    // --- System Inputs ---
    input wire          clk,                     // System clock (e.g., 50MHz)
    input wire          reset_n,                 // Asynchronous reset, active-low

    // --- OBC Interface ---
    input wire          obc_heartbeat_in,        // Heartbeat signal from OBC

    // --- Sensor Interface (from external ADCs) ---
    input wire [11:0]   adc_temp_data_in,        // 12-bit temperature data
    input wire [11:0]   adc_volt_data_in,        // 12-bit voltage data

    // --- Control Outputs ---
    output reg          obc_reset_out,           // To MOSFET gate for OBC reset
    output reg          battery_isolate_out      // To solid-state relay for power isolation
);

    // --- Parameters and Constants ---
    // Clock frequency dependent: assumes 50 MHz clock
    localparam CLOCK_FREQ_HZ = 50_000_000;
    localparam HEARTBEAT_TIMEOUT_CYCLES = CLOCK_FREQ_HZ * 10; // 10 seconds
    localparam RESET_PULSE_CYCLES       = CLOCK_FREQ_HZ / 4;  // 250 ms pulse

    // Thresholds for comparison (scaled for 12-bit ADC)
    // Example: For TMP36, 60°C -> 1.1V. With 3.3V ADC ref, value = (1.1/3.3)*4095 = 1365
    localparam TEMP_THRESHOLD_ADC       = 1365;
    // Example: For 3.2V battery with 2:1 divider -> 1.6V. With 3.3V ADC ref, value = (1.6/3.3)*4095 = 1985
    localparam VOLT_THRESHOLD_ADC       = 1985;
    
    // --- Internal Registers and Wires ---
    reg  [31:0] heartbeat_timer;
    reg         prev_heartbeat_state;
    reg         armed_state;

    // AI engine instance (would be a complex, generated IP block)
    wire        ai_thermal_alert;
    ai_inference_engine_core u_ai_core (
        .clk(clk),
        .reset_n(reset_n),
        .temp_data_in(adc_temp_data_in),
        .volt_data_in(adc_volt_data_in),
        .thermal_alert_out(ai_thermal_alert)
    );

    // --- Heartbeat Monitoring FSM ---
    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            heartbeat_timer <= 0;
            prev_heartbeat_state <= 1'b0;
            obc_reset_out <= 1'b0;
        end else if (armed_state) begin
            // Reset timer on any change in the heartbeat signal
            if (obc_heartbeat_in != prev_heartbeat_state) begin
                heartbeat_timer <= 0;
                prev_heartbeat_state <= obc_heartbeat_in;
            end else begin
                // Increment timer if no change
                if (heartbeat_timer < HEARTBEAT_TIMEOUT_CYCLES) begin
                    heartbeat_timer <= heartbeat_timer + 1;
                end
            end

            // Trigger reset if timer exceeds timeout
            if (heartbeat_timer >= HEARTBEAT_TIMEOUT_CYCLES) begin
                obc_reset_out <= 1'b1;
            end
            
            // De-assert reset after pulse duration is met
            if (heartbeat_timer >= (HEARTBEAT_TIMEOUT_CYCLES + RESET_PULSE_CYCLES)) begin
                obc_reset_out <= 1'b0;
                heartbeat_timer <= 0; // Reset timer to re-arm monitoring
            end
        end
    end

    // --- EPS Monitoring and System Arming Logic ---
    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            armed_state <= 1'b1; // System is armed on reset
            battery_isolate_out <= 1'b0; // Power is ON by default
        end else if (armed_state) begin
            // Check for critical events. These are latched and unrecoverable without a hard reset.
            if ((adc_temp_data_in > TEMP_THRESHOLD_ADC) || 
                (adc_volt_data_in < VOLT_THRESHOLD_ADC) || 
                (ai_thermal_alert == 1'b1)) 
            begin
                battery_isolate_out <= 1'b1; // Latch: Command battery isolation
                armed_state <= 1'b0;         // Disarm the system permanently
            end
        end
    end

endmodule

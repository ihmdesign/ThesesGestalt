/* 
 * File:   main.c
 * Author: MasonC
 *
 * Created on November 8, 2022, 10:19 PM
 */

// PIC16F18313 Configuration Bit Settings

// 'C' source line config statements

// CONFIG1
#pragma config FEXTOSC = OFF    // FEXTOSC External Oscillator mode Selection bits (Oscillator not enabled)
#pragma config RSTOSC = HFINT32  // Power-up default value for COSC bits (HFINTOSC (1MHz))
#pragma config CLKOUTEN = OFF   // Clock Out Enable bit (CLKOUT function is disabled; I/O or oscillator function on OSC2)
#pragma config CSWEN = OFF      // Clock Switch Enable bit (The NOSC and NDIV bits cannot be changed by user software)
#pragma config FCMEN = OFF      // Fail-Safe Clock Monitor Enable (Fail-Safe Clock Monitor is disabled)

// CONFIG2

#include <xc.h>
#include <stdint.h>
#include <stdlib.h>
#define _XTAL_FREQ  32000000     // Set clock frequency to 1 MHz

uint8_t mode = 0; //0 for squre-pwm, 1 for sine-pwm
uint8_t buffer = 0;//uart recv buffer

int duty_index = 16; //0-3 corresponding 3/16, 7/16, 11/16, 15/16 of duty cycle for square wave
                                          //12.5%, 25%, 50%, 100% for sine wave 
uint8_t freq_index = 4; //0-7 modes of frequency adjustments

uint8_t polarity = 0; //output polarity
// Sine table contains pre-calculated values of sin(x)
//resolution: 64
uint8_t sine_table[] = {
128,134,141,147,153,159,165,171,
177,183,188,194,199,204,209,214,
219,223,227,231,234,238,241,244,
246,249,250,252,254,255,255,255,
255,255,255,255,254,252,250,249,
246,244,241,238,234,231,227,223,
219,214,209,204,199,194,188,183,
177,171,165,159,153,147,141,134,
128,122,115,109,103,97,91,85,
79,73,68,62,57,52,47,42,
37,33,29,25,22,18,15,12,
10,7,6,4,2,1,1,1,
0,0,1,1,2,4,6,7,
10,12,15,18,22,25,29,33,
37,42,47,52,57,62,68,73,
79,85,91,97,103,109,115,122};

uint16_t PR_val[] = {173, 129, 111, 97, 86, 77, 64, 59}; // for 90, 120, 140, 160, 180, 200, 240, 260hz
// Index into sine table
uint16_t index = 0;

// Initialize CCP Module
void init_ccp_cwg(void) {
    // Set PA0, PA1 Pin as output
    TRISA0 = 1;
    TRISA1 = 1;
    ANSELA = 0; // all digital
    WPUA = 0; // weak pullup
    //RA1PPS = 12; // Output CCP1 to RA1
    RA1PPS = 0b01000; //get cwg1a
    RA0PPS = 0b01001;//get cwg1b
    // Set CCP1CON register to PWM mode
    CCP1CON = 0b10011111;//FMT = 1
    CCP1IE = 1;
    CCP1IF = 1;
    // Enable Global Interrupts
    GIE = 1;
    
    // Enable Peripheral Interrupts
    PEIE = 1;
    TMR2IE = 1; //enable interrupt on timer2
    // Set PR2 with appropriate PWM period
    
    // Set Timer2 Control Register
    T2CON = 0b00000110; // Timer 2 PS1/16 setting
    PR2 = PR_val[freq_index];
    
    //set cwg
    CWG1CON0 = 0b01000100;//half bridge, disable
    CWG1CON1 = 0;//A--non-invert, B--invert, C--non-invert, D--invert
    CWG1DAT = 0b00000011;//set data input to ccp1
    CWG1AS0 = 0b01111000;//disable autoshutdown, all 0 when shutdown occurs
    CWG1DBF = 0b0;
    CWG1DBR = 0b0;
    CWG1CLKCON = 0; //select system clk
    CWG1CON0bits.EN = 1;
    TRISA0 = 0;
    TRISA1 = 0;
    
    
    __delay_us(50);
}



// Timer2 Interrupt Service Routine
void __interrupt() ISR(void) {
        if(mode == 1 && CCP1IF){ //spwm
            // Clear Timer2 Interrupt Flag

            T2CON = 0b00000101;// Timer 2 PS1/4 setting
            PR2 = PR_val[freq_index]; //load freq
            // Update Duty Cycle
            uint8_t loadval = sine_table[index>>1];
            loadval = (uint8_t)(((uint16_t) loadval * (PR_val[freq_index])) >> 8);
            index = (index + 1) % 256;
            if(loadval == 0){ //prevent 0 duty cycle loaded
                CCPR1H = 0x00;
                CCPR1L= 64;
            }
            else{
                CCPR1H = loadval;
                CCPR1L= 0x00;
            }
            CCP1IF = 0; //clear flag
        }
        else if(mode == 0 && CCP1IF){
            //square
            //T2CON = 0b00000110;// Timer 2 PS1/64 setting
            //PR2 = PR_val[freq_index]; //load freq
            // Update Duty Cycle
            index = (index + 1) % 31;
            CCPR1H = 0x00;
            CCPR1L= 64;
            if((CWG1CON1 == 0b10) && ((index - 16) < duty_index || (index < duty_index))){
                CWG1CON0bits.EN = 0;
                CWG1CON1 = 0;
                CWG1CON0bits.EN = 1;
            }
            else if((CWG1CON1 == 0) && ((index < 16 && index > duty_index) || (index > (duty_index + 16) && index < 32))){
                CWG1CON0bits.EN = 0;
                CWG1CON1 = 0b10;
                CWG1CON0bits.EN = 1;
            }
            if(index < duty_index)
            {
                CCPR1H = (PR_val[freq_index]);
                CCPR1L= 0x00;
            }
            else{
                CCPR1H = 0x00;
                CCPR1L= 64;
            }

            CCP1IF = 0; //clear flag
        }
    
}
void UART_Write(unsigned char data) {
   // while(!TRMT){};

    TX1REG = data;
}
void main(void) {

    // Initialize CCP Module
    TRISA4 = 0;
    LATA4 = 1;
    init_ccp_cwg();


    // Enable Timer2 Interrupts
   
    // Infinite loop
    while(1) {

       
    }
    
    return;
}

/* 
 * File:   main.c
 * Author: MasonC
 *
 * Created on November 8, 2022, 10:19 PM
 */

#include <stdio.h>
#include <stdlib.h>




// PIC16F18313 Configuration Bit Settings

// 'C' source line config statements

// CONFIG1
#pragma config FEXTOSC = OFF    // FEXTOSC External Oscillator mode Selection bits (Oscillator not enabled)
#pragma config RSTOSC = HFINT32  // Power-up default value for COSC bits (HFINTOSC (1MHz))
#pragma config CLKOUTEN = OFF   // Clock Out Enable bit (CLKOUT function is disabled; I/O or oscillator function on OSC2)
#pragma config CSWEN = OFF      // Clock Switch Enable bit (The NOSC and NDIV bits cannot be changed by user software)
#pragma config FCMEN = OFF      // Fail-Safe Clock Monitor Enable (Fail-Safe Clock Monitor is disabled)

// CONFIG2
#pragma config MCLRE = ON       // Master Clear Enable bit (MCLR/VPP pin function is MCLR; Weak pull-up enabled )
#pragma config PWRTE = OFF      // Power-up Timer Enable bit (PWRT disabled)
#pragma config WDTE = ON       // Watchdog Timer Enable bits (WDT disabled; SWDTEN is ignored)
#pragma config LPBOREN = OFF    // Low-power BOR enable bit (ULPBOR disabled)
#pragma config BOREN = OFF      // Brown-out Reset Enable bits (Brown-out Reset disabled)
#pragma config BORV = LOW       // Brown-out Reset Voltage selection bit (Brown-out voltage (Vbor) set to 2.45V)
#pragma config PPS1WAY = OFF    // PPSLOCK bit One-Way Set Enable bit (The PPSLOCK bit can be set and cleared repeatedly (subject to the unlock sequence))
#pragma config STVREN = ON      // Stack Overflow/Underflow Reset Enable bit (Stack Overflow or Underflow will cause a Reset)
#pragma config DEBUG = OFF      // Debugger enable bit (Background debugger disabled)

// CONFIG3
#pragma config WRT = OFF        // User NVM self-write protection bits (Write protection off)
#pragma config LVP = OFF         // Low Voltage Programming Enable bit (Low voltage programming enabled. MCLR/VPP pin function is MCLR. MCLRE configuration bit is ignored.)

// CONFIG4
#pragma config CP = OFF         // User NVM Program Memory Code Protection bit (User NVM code protection disabled)
#pragma config CPD = OFF        // Data NVM Memory Code Protection bit (Data NVM code protection disabled)

// #pragma config statements should precede project file includes.
// Use project enums instead of #define for ON and OFF.
#include <xc.h>
#include <stdint.h>
#include <stdlib.h>
#define _XTAL_FREQ  32000000     // Set clock frequency 

uint8_t mode = 0; //0 for squre-pwm, 1 for sine-pwm
uint8_t buffer = 0;//uart recv buffer

uint8_t duty_index = 2; //0-3 corresponding 3/16, 7/16, 11/16, 15/16 of duty cycle for square wave
                                          //12.5%, 25%, 50%, 100% for sine wave 
uint8_t freq_index = 3; //0-3 modes of frequency adjustments


// Sine table contains pre-calculated values of sin(x)
//resolution: 32
uint8_t sine_table[] = {
128,134,140,146,152,158,165,170,
176,182,188,193,198,203,208,213,
218,222,226,230,234,237,240,243,
245,248,250,251,253,254,254,255,
255,255,254,254,253,251,250,248,
245,243,240,237,234,230,226,222,
218,213,208,203,198,193,188,182,
176,170,165,158,152,146,140,134,
128,121,115,109,103,97,90,85,
79,73,67,62,57,52,47,42,
37,33,29,25,21,18,15,12,
10,7,5,4,2,1,1,0,
0,0,1,1,2,4,5,7,
10,12,15,18,21,25,29,33,
37,42,47,52,57,62,67,73,
79,85,90,97,103,109,115,121};

uint16_t PR_val[] = {173, 111, 92, 64}; // for 90, 140, 180 240hz
// Index into sine table
uint8_t index = 0;
uint16_t loadval;
uint8_t state = 0; //is the board being addressed by the controller

void init_ccp_cwg(void) {
    // Set PA0, PA1 Pin as output
    TRISA0 = 1;//first set the flag to disable PA0 and PA1 outputs
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
    T2CON = 0b00000010; // Timer 2 PS1/16 setting
    PR2 = PR_val[freq_index];
    
    //set cwg
  
    CWG1CON0 = 0b01000100;//half bridge, disable
    CWG1CON1 = 0;//A--non-invert, B--invert, C--non-invert, D--invert
    CWG1DAT = 0b00000011;//set data input to ccp1
    CWG1AS0 = 0b01111000;//disable autoshutdown, all 0 when shutdown occurs
    CWG1DBR = 0b0;
    CWG1DBF = 0b0;
    CWG1CLKCON = 1; //select hfint clk
    CWG1CON0bits.EN = 1;
    __delay_us(100);
}

void usart_init() {
    TRISA5 = 1; //port 5 as RXinput
    TRISA2 = 1; //port 2 as TXout
    ANSELA = 0;
    RXPPS = 0b00101; //port5 RX
    RA2PPS = 0b10100; //port2 TX

    RC1STA = 0b10010000; // 8 bit continuous reception CREN = 1 SPEN = 1
    TX1STA = 0b00100100; // Asynchronous reception High Baud Rate selection BRGH = 1  TXEN = 1; //transmit enable //async mode
    BAUD1CON = 0b00001000; // 16 bit SPBRG   BRG16 = 1
    SP1BRGH = 0;
    SP1BRGL = 68; // 115.2k baud rate
    TX9 = 1; //enable 9bit transmission
    RX9 = 1; //enable 9-bit recv
    RCIE = 1; //receive interrupt enable
    //IDLEN = 1; // Idle inhibits the CPU clk

    __delay_us(100); //wait for set up

}
uint8_t make_addr_byte(uint8_t start, uint8_t addr){
    //make the first, address byte for transmission
    uint8_t addr_byte = 0;
    addr_byte |= (start & 0b1);
    addr_byte |= (addr << 1);
   
    return addr_byte;
}
uint8_t getParity(uint8_t n)
{ //return the parity of n. if odd, return 1, even, return 0
    uint8_t parity = 0;
    while (n)
    {
        parity = !parity;
        n = n & (n - 1);
    }
    return (parity & 0b1);
}

void UART_Write(uint8_t data) {
    while(!TRMT){};
    
    TX9D = (getParity(data) & 0b1);
    TX1REG = data;
    
}

// Timer2 Interrupt Service Routine
void __interrupt() ISR(void) {

        if (RCIF) {
            RCIF = 0; // Clear The Flag
            uint8_t parity = RX9D; //read the 9th parity
            buffer = RC1REG; // Read The Received Data Buffer
            if(getParity(buffer) != parity) return; //drop packet
            
            if((buffer >> 7) != 0b1){ //addr byte recved
                uint8_t addr = (buffer >> 1); //get addr
                uint8_t start = (buffer & 0b1); //get start/stop
                if(addr != 0){ //not the current address
                    --addr; //decrease addr
                    UART_Write(make_addr_byte(start, addr)); //send
                 return;   
                }
                else{ //the current addr
                    LATA4 = start; //LED on/off
                    state = start; 
                    if(start == 0){
                        TMR2ON = 0;//ccp enable 
                        TRISA0 = 1;
                        TRISA1 = 1;
                    }
                    return;
                    }
            
            }
            else { //data byte received
                if(state == 0){ //previous data byte not address to this board
                      while(!TRMT){};
                      TX9D = parity;
                      TX1REG = buffer;//transmit directly
                      return;
                }
                else{ //data byte addressed to this board
                    TRISA1 = 0;
                    TRISA0 = 0;
                    TMR2ON = 1;
                    mode = (buffer & 0b1);
                    if (mode){
                        T2CON = 0b00000101;
                    }
                    else
                        T2CON = 0b00000110;
                    freq_index = (buffer & 0b110) >> 1;
                    duty_index = (buffer & 0b1111000) >> 3;
                    PR2 = PR_val[freq_index]; //load freq
                    state = 0;//state flipped to 0 again
                    return;
                }
            }
        }

        else if(CCP1IF && mode){ //spwm
            
            //PR2 = PR_val[freq_index]; //load freq
            // Update Duty Cycle
            CCP1IF = 0; //clear flag
            TMR2IF = 0;
            index = (index + 1) % 128;
            loadval = sine_table[index] >> (8 - duty_index);
            loadval = ( loadval * (PR_val[freq_index])) >> 8;
            CCPR1H = loadval;
            CCPR1L= 0x64;
            
            //return;
        
        }
        else if(CCP1IF &&(!mode)){
           
           //square
            //T2CON = 0b00000110;// Timer 2 PS1/64 setting
            //PR2 = PR_val[freq_index]; //load freq
            // Update Duty Cycle
            CCP1IF = 0; //clear flag
            TMR2IF = 0;
            index = (index + 1) % 31;
            if((index == 0) || (index == 15)){
                CWG1CON0bits.EN = 0;
                CWG1CON1bits.POLB= 0;
                CWG1CON0bits.EN = 1;
            }
            else if(index == duty_index || index == (duty_index + 15) || duty_index == 0){
                CWG1CON0bits.EN = 0;
                CWG1CON1bits.POLB = 1;
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

            
        }
    
}

int main(int argc, char** argv) {

    // Initialize CCP Module
    TRISA4 = 0;
    WDTCON = 0b100011;
    init_ccp_cwg();
    usart_init();


    // Enable Timer2 Interrupts
   
    // Infinite loop
    while(1) {
        CLRWDT();
       
    }
    
}

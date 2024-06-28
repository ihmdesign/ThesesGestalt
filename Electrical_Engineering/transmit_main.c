

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
#pragma config MCLRE = ON       // Master Clear Enable bit (MCLR/VPP pin function is MCLR; Weak pull-up enabled )
#pragma config PWRTE = OFF      // Power-up Timer Enable bit (PWRT disabled)
#pragma config WDTE = OFF       // Watchdog Timer Enable bits (WDT disabled; SWDTEN is ignored)
#pragma config LPBOREN = OFF    // Low-power BOR enable bit (ULPBOR disabled)
#pragma config BOREN = OFF      // Brown-out Reset Enable bits (Brown-out Reset disabled)
#pragma config BORV = LOW       // Brown-out Reset Voltage selection bit (Brown-out voltage (Vbor) set to 2.45V)
#pragma config PPS1WAY = OFF    // PPSLOCK bit One-Way Set Enable bit (The PPSLOCK bit can be set and cleared repeatedly (subject to the unlock sequence))
#pragma config STVREN = ON      // Stack Overflow/Underflow Reset Enable bit (Stack Overflow or Underflow will cause a Reset)
#pragma config DEBUG = OFF      // Debugger enable bit (Background debugger disabled)

// CONFIG3
#pragma config WRT = OFF        // User NVM self-write protection bits (Write protection off)
#pragma config LVP = ON         // Low Voltage Programming Enable bit (Low voltage programming enabled. MCLR/VPP pin function is MCLR. MCLRE configuration bit is ignored.)

// CONFIG4
#pragma config CP = OFF         // User NVM Program Memory Code Protection bit (User NVM code protection disabled)
#pragma config CPD = OFF        // Data NVM Memory Code Protection bit (Data NVM code protection disabled)


#include <xc.h>
#include <stdint.h>
#include <stdlib.h>
#define _XTAL_FREQ  16000000     // Set clock frequency to 1 MHz

uint8_t mode = 0; //0 for squre-pwm, 1 for sine-pwm
uint8_t buffer = 0;//uart recv buffer

uint8_t duty_index = 2; //0-3 corresponding 3/16, 7/16, 11/16, 15/16 of duty cycle for square wave
                                          //12.5%, 25%, 50%, 100% for sine wave 
uint8_t duty_array[] = {3, 7, 11, 15};
uint8_t freq_index = 3; //0-3 modes of frequency adjustments


// Sine table contains pre-calculated values of sin(x)
//resolution: 64
uint8_t sine_table[] = {
128,140,152,165,176,188,198,208,
218,226,234,240,245,250,253,254,
255,254,253,250,245,240,234,226,
218,208,198,188,176,165,152,140,
128,115,103,90,79,67,57,47,
37,29,21,15,10,5,2,1,
0,1,2,5,10,15,21,29,
37,47,57,67,79,90,103,115
    };
uint8_t PR_val[] = {173, 111, 86, 64}; // for 90, 140, 180 240hz
// Index into sine table
uint8_t index = 0;

// Initialize CCP Module
void init_ccp(void) {
    // Set PA0, PA1 Pin as output
    TRISA1 = 0;
    TRISA0 = 0;
    RA1PPS = 12; // Output CCP1 to RA0
    //RA0PPS = 12;
    // Set CCP1CON register to PWM mode
    CCP1CON = 0b10011111;//FMT = 1
    CCP1IE = 1;
    CCP1IF = 1;
    // Enable Global Interrupts
    GIE = 1;
    
    // Set PR2 with appropriate PWM period
    
    // Set Timer2 Control Register
    T2CON = 0b00000110; // Timer 2 PS1/16 setting
    PR2 = PR_val[freq_index];
    __delay_ms(50);
}

void usart_init() {
    TRISA5 = 1; //port 5 as RXinput
    TRISA2 = 1; //port 2 as TXout
    
    RXPPS = 0b00101; //port5 RX
    RA2PPS = 0b10100; //port2 TX

    RC1STA = 0b10010000; // 8 bit continuous reception CREN = 1 SPEN = 1
    TX1STA = 0b00100100; // Asynchronous reception High Baud Rate selection BRGH = 1  TXEN = 1; //transmit enable //async mode
    BAUD1CON = 0b00001000; // 16 bit SPBRG   BRG16 = 1
    SP1BRGH = 0;
    SP1BRGL = 68; // 115.2k baud rate
    TX9 = 1; //enable 9bit transmission
    RCIE = 1; //receive interrupt enable
    PEIE = 1;
    //IDLEN = 1; // Idle inhibits the CPU clk

    __delay_ms(50); //wait for set up

}

uint8_t getParity(uint8_t n)
{ //return the parity of n. if odd, return 1, even, return 0
    uint8_t parity = 0;
    while (n)
    {
        parity = !parity;
        n = n & (n - 1);
    }
    return parity;
}

uint8_t make_addr_byte(uint8_t addr, uint8_t start){
    //make the first, address byte for transmission
    //96 device addressable
    uint8_t addr_byte = 0;
    addr_byte |= (start & 0b1);
    addr_byte |= (addr << 1);
   
    return addr_byte;
}

uint8_t make_data_byte(uint8_t duty, uint8_t freq, uint8_t mode){
    //make the second, data byte for transmission 
    uint8_t data_byte = 0;
    data_byte |= 0b11 << 6; //differentiate btw byte1 and 2
    data_byte |= ((duty & 0b11) << 4);
    data_byte |= ((freq & 0b11) << 2);
    data_byte |= (mode & 0b11);
    
    return data_byte;
}

// Timer2 Interrupt Service Routine
void __interrupt() ISR(void) {
        if (RCIF) {
        
            RCIF = 0; // Clear The Flag
        }

        if(CCP1IF && mode){ //spwm
            // Clear Timer2 Interrupt Flag
            T2CON = 0b00000110;// Timer 2 PS1/16 setting
            PR2 = PR_val[freq_index]; //load freq
            // Update Duty Cycle
            ++index;
            if (index == 64) //wrap around
                index = 0;
            uint16_t loadval = sine_table[index] >> (3 - duty_index);
            loadval = loadval * (PR_val[freq_index]+1) / 255;
            if(loadval == 0){ //prevent 0 duty cycle loaded
                CCPR1H = 0x00;
                CCPR1L= 64;
            }
            else{
                CCPR1H = (uint8_t)loadval;
                CCPR1L= 0x00;
            }
            CCP1IF = 0; //clear flag
        }
        else if(CCP1IF &&(!mode)){
            T2CON = 0b00000111;// Timer 2 PS1/64 setting
            PR2 = PR_val[freq_index]; //load freq
            // Update Duty Cycle
            ++index;
            if (index == 16) //wrap around
                index = 0;
            
            if(index < duty_array[duty_index])
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
void UART_Write(uint8_t data) {
    while(!TRMT){};
    TX9D = getParity(data);
    TX1REG = data;
    
}
void main(void) {
    OSCFRQ = 0b0000110; //32Mhz
    // Initialize CCP Module
    usart_init();
    init_ccp();


    
    // Enable Timer2 Interrupts
   
    // Infinite loop
    while (1) {
        UART_Write(make_addr_byte(0, 1));
        UART_Write(make_data_byte(2, 0, 0));
        __delay_ms(100);
        UART_Write(make_addr_byte(0, 0));
        __delay_ms(100);
        UART_Write(make_addr_byte(2, 1));
        UART_Write(make_data_byte(0, 1, 1));
        __delay_ms(100);
        UART_Write(make_addr_byte(2, 0));
        __delay_ms(100);
        UART_Write(make_addr_byte(2, 1));
        UART_Write(make_data_byte(2, 1, 0));
        __delay_ms(100);
        UART_Write(make_addr_byte(2, 0));
        __delay_ms(100);
        UART_Write(make_addr_byte(3, 1));
        __delay_ms(100);
        UART_Write(make_data_byte(2, 1, 1));
         __delay_ms(200);
        UART_Write(make_addr_byte(3, 0));

        
    }
    
    return;
}

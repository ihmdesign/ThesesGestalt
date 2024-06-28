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

//uint8_t buffer = 0;//uart recv buffer
uint8_t state = 0;
uint8_t duty = 0;

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
    PEIE = 1;
    //IDLEN = 1; // Idle inhibits the CPU clk

    __delay_us(50); //wait for set up

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
    
    //TX9D = (getParity(data) & 0b1);
    TX1REG = data;
    
}



void main(void) {
    
    usart_init();
    TRISA0 = 1;
    ANSELA = 0b00000001;
    ADCON1 = 0b00010000;//ADFM = 0 left justified, ADC has fosc/2, vss = 0, vdd = vin
    ADCON0 = 0b00000001;

    ADCON0bits.ADON=1;
    __delay_us(100);
    ADCON0bits.GO_nDONE=1;
    uint16_t buffer = 0;
    while(1)
    {
        buffer = 0;
       for(uint8_t i = 0; i < 8; i++){
            ADCON0bits.GO_nDONE=1;
            buffer += ADRESH;
            __delay_ms(10);
        }

        UART_Write(buffer >> 3);
        //UART_Write(buffer2);
    }
    
}

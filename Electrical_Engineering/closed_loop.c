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

uint8_t buffer = 0;//uart recv buffer
uint8_t state = 0;
uint8_t received_duty = 0;
uint8_t load_duty = 0;

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
void init_ccp(void) {
    // Set PA0, PA1 Pin as output
    TRISA0 = 0;
    TRISA1 = 0;
    LATA0 = 1;
    LATA1 = 1;
    ANSELA = 0; // all digital
    WPUA = 0; // weak pullup
    //RA1PPS = 12; // Output CCP1 to RA1

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
    T2CON = 0b00000100; // Timer 2 PS1/1 setting
    PR2 = 32;
    //set cwg
  
 
    CWG1CON0 = 0b01000100;//half bridge, disable
    CWG1CON1 = 0;//A--non-invert, B--invert, C--non-invert, D--invert
    CWG1DAT = 0b00000011;//set data input to ccp1
    CWG1AS0 = 0b01111000;//disable autoshutdown, all 0 when shutdown occurs
    CWG1DBR = 0b1;
    CWG1DBF = 0b0;
    CWG1CLKCON = 1; //select hfint clk
    CWG1CON0bits.EN = 1;
    __delay_us(50);
}
void adc_init(){
    TRISA4 = 1;
    ANSELA = 0b00010000;
    ADCON1 = 0b00010000;//ADFM = 0 left justified, ADC has fosc/2, vss = 0, vdd = vin
    ADCON0 = 0b00010001;
    __delay_us(100);
    ADCON0bits.GO_nDONE=1;
}
uint8_t make_addr_byte(uint8_t start, uint8_t addr){
    //make the first, address byte for transmission
    //96 device addressable
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
                    state = start; 
                    if(start == 0){
                        TMR2ON = 0;//ccp disable 
                        RA1PPS = 0;
                        RA0PPS = 0;
                        LATA0 = 1;
                        LATA1 = 1;
                    }
                    return;
                    }
            
            }
            else { //data byte received
                if(state == 0){ //previous data byte not address to this board
                    while(!TRMT){};
                    TX9D = parity;
                    TX1REG = buffer;
                    return;
                }
                else{ //data byte addressed to this board
                    RA0PPS = 0b01000; //get cwg1a
                    RA1PPS = 0b01001;
                    CWG1CON0bits.EN = 1;
                    TMR2ON = 1;
                    received_duty = (buffer & 0b11111);
                    load_duty = received_duty;
                    PR2 = 32; //load freq
                    state = 0;//state flipped to 0 again
                    return;
                }
            }
        }

        if(CCP1IF){
            //square
            //T2CON = 0b00000101;// Timer 2 PS1/64 setting
            CCP1IF = 0; //clear flag
            TMR2IF = 0;
            // Update Duty Cycle
            CCPR1H = load_duty;
            CCPR1L= 64;

        }
    
}

void main(void) {
    //all digital at the beginning
    WDTCON = 0b100011;
    RA1PPS = 0;
    RA0PPS = 0;
    usart_init();
    init_ccp();
    adc_init();
    uint16_t adc_buffer = 0;
    
    while(1){
        CLRWDT();
        adc_buffer = 0;
        //get avg every eight times
        for(uint8_t i = 0; i < 2; i++){
            ADCON0bits.GO_nDONE=1;
            adc_buffer += ADRESH;
            __delay_us(5);
        }
        uint8_t read_val = adc_buffer >> 4; // >>3 >>3
        if(read_val < received_duty - 1){
            if(load_duty < 31)
                ++load_duty;
        }
        else if(read_val > received_duty + 1){
            if(load_duty > 0)
                --load_duty;
        }
       
    }
}

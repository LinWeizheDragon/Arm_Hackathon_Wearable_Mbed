//----------------------------------------------------------------------------
// The confidential and proprietary information contained in this file may
// only be used by a person authorised under and to the extent permitted
// by a subsisting licensing agreement from ARM Limited or its affiliates.
//
// (C) COPYRIGHT 2016 ARM Limited or its affiliates.
// ALL RIGHTS RESERVED
//
// This entire notice must be reproduced on all copies of this file
// and copies of this file may only be made by a person if such person is
// permitted to do so under the terms of a subsisting license agreement
// from ARM Limited or its affiliates.
//----------------------------------------------------------------------------
#include "mbed.h"
#include "C12832.h"
#include "OdinWiFiInterface.h"
#include "MQTTNetwork.h"
#include "MQTTmbed.h"
#include "MQTTClient.h"
#include <string>
#include "MMA7660.h"
#include <iostream>
#include <sstream>
#include "Sht31.h"
#include "CCS811.h"
#include <stdlib.h>
#include <stdio.h>
//#include <omp.h>

#define USE_I2C_2V8

using namespace std;

// GLOBAL VARIABLES HERE
C12832  lcd(PE_14, PE_12, PD_12, PD_11, PE_9);

OdinWiFiInterface wifi;
InterruptIn button1(PF_2);
InterruptIn button2(PG_4);
volatile bool publish = false;
volatile int message_num = 0;
const char* host = "m23.cloudmqtt.com";

int index = 0;

MMA7660 accel(PF_0, PF_1);

Sht31   temp_sensor(PF_0, PF_1);
CCS811  air_sensor(PF_0, PF_1);

// FUNCTION DEFINITIONS HERE
void lcd_print(const char* message) {
    lcd.cls();
    lcd.locate(0, 0);
    lcd.printf(message);
}
void publish_message() {
    publish = true;
    lcd_print("Recording started.");
}

void publish_message_stop()
{
    publish = false;
    lcd_print("Recording stopped.");
}

string read_temp() {
    float t = temp_sensor.readTemperature();
    float h = temp_sensor.readHumidity();
    string result;
    stringstream temp;
    temp << "Temp: " << t << " Humi: " << h;
    result = temp.str();
    return result;
}

string read_air() {
    air_sensor.init();
    uint16_t eco2, tvoc;
    air_sensor.readData(&eco2, &tvoc);
    
    string result;
    stringstream temp;
    temp << "eco2: " << eco2 << " tvoc: " << tvoc;
    result = temp.str();
    return result;
}

void messageArrived(MQTT::MessageData& md) {
    MQTT::Message &message = md.message;
    //char msg[300];
    //sprintf(msg, "Message arrived: QoS%d, retained %d, dup %d, packetID %d\r\n", message.qos, message.retained, message.dup, message.id);
    //lcd_print(msg);
    //wait_ms(1000);
    string pyl = (char*)message.payload ;
    int a = pyl.find(" ");
    string str_a = pyl.substr(0, a);
    
    if ( str_a == "T" ){
        //publish = false;
        //string str_f = pyl.substr(15, str_f.size());
        int b = pyl.find(" ",15);
        string str_temp = read_temp();
        string str_air = read_air();
        string combine = pyl.substr( 2 , b-2 ) + "\n" + str_temp;
        lcd_print(combine.c_str());
        //lcd_print(combine.c_str()) ;
    }
    
    else if (str_a == "D")
    {
        lcd.cls();
        //publish = true;
    }
    
    
    
}



string read_accel() {
    float x = accel.x();
    float y = accel.y();
    float z = accel.z();
    string result;
    stringstream temp;
    temp << index << " " << x << " " << y << " " << z;
    result = temp.str();
    return result;
}




int main() {
    
    // MAIN CODE HERE
    lcd_print("Connecting...");
    int ret = wifi.connect(MBED_CONF_APP_WIFI_SSID, MBED_CONF_APP_WIFI_PASSWORD, NSAPI_SECURITY_WPA_WPA2);
    if (ret != 0) {
        lcd_print("Connection error.");
        return -1;
    }
    lcd_print("Successfully connected!");
    
    NetworkInterface* net = &wifi;
    MQTTNetwork mqttNetwork(net);
    MQTT::Client<MQTTNetwork, Countdown> client(mqttNetwork);
    
    const char* host = "m23.cloudmqtt.com";
    const char* topic = "python/test";
    lcd_print("Connecting to MQTT network...");
    int rc = mqttNetwork.connect(host, 13299);
    if (rc != 0) {
        lcd_print("Connection error.");
        return -1;
    }
    lcd_print("Successfully MQTT connected!");
    
    
    MQTTPacket_connectData data = MQTTPacket_connectData_initializer;
    data.MQTTVersion = 3;
    data.clientID.cstring = "connect-cloud-board";
    data.username.cstring = "frylvkng";  // Your mqtt username if required
    data.password.cstring = "WWqMi9zd5xEa"; // Your mqtt password if required
    client.connect(data);
    client.subscribe(topic, MQTT::QOS0, messageArrived);
    
    
    button1.fall(&publish_message);
    
    while (true) {
        // WHILE LOOP CODE HERE
        //client.yield(10);
        if (publish) {
            //lcd_print("sending started!");
            
            MQTT::Message message;
            MQTT::Message message2;
            
            index = 0;
            
            while(index < 500000)
            {
                
                index++;
                
                string acc = read_accel();
                //string tnh = read_temp();
                //string air = read_air();
                //light_sensor.begin();
                //light_sensor.setGain(TSL2561_GAIN_0X);
                //light_sensor.setTiming(TSL2561_INTEGRATIONTIME_13MS);
                //string light = read_light();
                //string laser = read_laser();
                string result = acc;
                // + light + laser;
                
                const char* tempString = result.c_str();
                
                message.qos = MQTT::QOS0;
                message.retained = false;
                message.dup = false;
                message.payload = (void*)tempString;
                message.payloadlen = result.size();
                rc = client.publish(topic, message);
                
                
                if (index%250 == 0)
                {
                    string air_result = read_air();
                    
                    int first_space = air_result.find(" ", 9);
                    
                    
                    
                    if ( air_result.substr(8, first_space) != "65021" )
                    {
                        
                        string feed_air = "C "+air_result;
                        
                        const char* tempString2 = feed_air.c_str();
                        
                        message2.qos = MQTT::QOS0;
                        message2.retained = false;
                        message2.dup = false;
                        message2.payload = (void*)tempString2;
                        message2.payloadlen = feed_air.size();
                        rc = client.publish(topic, message2);
                        
                    }
                    
                    
                }
                
                
                client.yield(1);
                button2.fall(&publish_message_stop);
                if(publish == false)
                {
                    break;
                }
                
            }
            
            
            lcd_print("sending finished!");
            publish = false;
        }
    }
}

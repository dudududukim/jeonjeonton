// L298N 모터 드라이버 제어 핀 설정
const int ACT1_IN1 = 2, ACT1_IN2 = 3, ENA_ACT1 = 9;
const int ACT2_IN1 = 4, ACT2_IN2 = 5, ENA_ACT2 = 10;
const int ACT3_IN1 = 6, ACT3_IN2 = 7, ENA_ACT3 = 11;
const int ACT4_IN1 = 8, ACT4_IN2 = 12, ENA_ACT4 = 13;
const int ACT5_IN1 = A0, ACT5_IN2 = A1, ENA_ACT5 = A2;
const int ACT6_IN1 = A3, ACT6_IN2 = A4, ENA_ACT6 = A5; // 6번 액추에이터 추가

String inputCommand = "";
bool commandComplete = false;

void setup() {
  Serial.begin(9600);
  
  // 모든 액추에이터 핀 초기화
  initializeActuator(ACT1_IN1, ACT1_IN2, ENA_ACT1);
  initializeActuator(ACT2_IN1, ACT2_IN2, ENA_ACT2);
  initializeActuator(ACT3_IN1, ACT3_IN2, ENA_ACT3);
  initializeActuator(ACT4_IN1, ACT4_IN2, ENA_ACT4);
  initializeActuator(ACT5_IN1, ACT5_IN2, ENA_ACT5);
  initializeActuator(ACT6_IN1, ACT6_IN2, ENA_ACT6);
  
  Serial.println("Arduino Ready - Waiting for commands...");
}

void initializeActuator(int in1, int in2, int enable) {
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  pinMode(enable, OUTPUT);
  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(enable, HIGH);
}

void loop() {
  // 시리얼 명령 처리
  if (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      commandComplete = true;
    } else {
      inputCommand += inChar;
    }
  }
  
  // 명령 실행
  if (commandComplete) {
    processCommand(inputCommand);
    inputCommand = "";
    commandComplete = false;
  }
}

void processCommand(String command) {
  Serial.println("Received: " + command);
  
  if (command.startsWith("POP:")) {
    // 액추에이터 올리기: "POP:1,3,5"
    String actuatorList = command.substring(4);
    executeActuators(actuatorList, true);
    
  } else if (command.startsWith("DOWN:")) {
    // 액추에이터 내리기: "DOWN:1,3,5"  
    String actuatorList = command.substring(5);
    executeActuators(actuatorList, false);
    
  } else if (command == "STOP:ALL") {
    // 모든 액추에이터 정지
    stopAllActuators();
    Serial.println("All actuators stopped");
    
  } else {
    Serial.println("Unknown command: " + command);
  }
}

void executeActuators(String actuatorList, bool popUp) {
  // 쉼표로 구분된 액추에이터 ID들 파싱
  int startIndex = 0;
  int commaIndex = actuatorList.indexOf(',');
  
  String action = popUp ? "Popping up" : "Pulling down";
  Serial.println(action + " actuators: " + actuatorList);
  
  while (startIndex < actuatorList.length()) {
    String actuatorId;
    
    if (commaIndex == -1) {
      // 마지막 ID
      actuatorId = actuatorList.substring(startIndex);
      startIndex = actuatorList.length();
    } else {
      // 중간 ID
      actuatorId = actuatorList.substring(startIndex, commaIndex);
      startIndex = commaIndex + 1;
      commaIndex = actuatorList.indexOf(',', startIndex);
    }
    
    // 액추에이터 제어
    int id = actuatorId.toInt();
    controlActuator(id, popUp);
  }
  
  // 6초 동작
  delay(6000);
  
  // 모든 액추에이터 정지
  stopAllActuators();
  
  Serial.println("Action completed");
}

void controlActuator(int id, bool popUp) {
  int in1, in2, enable;
  
  // 액추에이터별 핀 할당
  switch (id) {
    case 1: in1 = ACT1_IN1; in2 = ACT1_IN2; enable = ENA_ACT1; break;
    case 2: in1 = ACT2_IN1; in2 = ACT2_IN2; enable = ENA_ACT2; break;
    case 3: in1 = ACT3_IN1; in2 = ACT3_IN2; enable = ENA_ACT3; break;
    case 4: in1 = ACT4_IN1; in2 = ACT4_IN2; enable = ENA_ACT4; break;
    case 5: in1 = ACT5_IN1; in2 = ACT5_IN2; enable = ENA_ACT5; break;
    case 6: in1 = ACT6_IN1; in2 = ACT6_IN2; enable = ENA_ACT6; break;
    default:
      Serial.println("Invalid actuator ID: " + String(id));
      return;
  }
  
  if (popUp) {
    // 올리기
    digitalWrite(in1, HIGH);
    digitalWrite(in2, LOW);
  } else {
    // 내리기
    digitalWrite(in1, LOW);
    digitalWrite(in2, HIGH);
  }
  
  Serial.println("Actuator " + String(id) + " " + (popUp ? "up" : "down"));
}

void stopAllActuators() {
  // 모든 액추에이터 정지
  digitalWrite(ACT1_IN1, LOW); digitalWrite(ACT1_IN2, LOW);
  digitalWrite(ACT2_IN1, LOW); digitalWrite(ACT2_IN2, LOW);
  digitalWrite(ACT3_IN1, LOW); digitalWrite(ACT3_IN2, LOW);
  digitalWrite(ACT4_IN1, LOW); digitalWrite(ACT4_IN2, LOW);
  digitalWrite(ACT5_IN1, LOW); digitalWrite(ACT5_IN2, LOW);
  digitalWrite(ACT6_IN1, LOW); digitalWrite(ACT6_IN2, LOW);
}


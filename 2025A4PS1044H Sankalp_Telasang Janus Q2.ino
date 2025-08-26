// C++ code
//

/* The force sensor pin should be pretty self explanatory.
The ascending pin is the pin connected to the LED that 
will light up when ascending, and the descending one will
light up while descending. The piezo pin is the pin attached
to the piezo electric buzzer. */
int force_sensor_pin = A0;
int ascending_pin = 2;
int descending_pin = 3;
int piezo_pin = 4;


/* Here we begin a serial connection, which is only used for 
debugging. We then configure all the pins to their I/O mode */
void setup()
{
  Serial.begin(9600);
  pinMode(force_sensor_pin, INPUT);
  pinMode(descending_pin, OUTPUT);
  pinMode(ascending_pin, OUTPUT);
  pinMode(piezo_pin, OUTPUT);
  noTone(piezo_pin);
}

// Initiallizing all the variables we will be using:

int delta = 0; /* This is the change in the force sensor 
value from the previously measured value */

int num_deltas = 20;

int delta_list[20] = {0}; /* The queue we will be recording 
our delta values in */

int pointer = 0; /* The pointer variable is how we will get
a queue like behaviour from an array. The pointer is the index
that we are currently on, and it will rotate around
the array, erasing and writing values as it goes. */

int pushed_delta = 0; /* This is the variable we will use 
to read the last element from delta_list */

int prev_force = 0; /* Stores the force value from the previous
iteration */

int curr_decreasing = 0; /* The total of the past 20 deltas which
are negative */

int curr_increasing = 0; /* The total of the past 20 deltas which
are positive */

int raw_force = 0; /* The raw reading from the force sensor */

int smoothed_force = 0; /* The reading from the force sensor
after filtering out some noise */

/* These booleans will be used for deciding when we 
have reached the apex */
bool ascending = false;
bool descending = false;
bool was_ascending = false;
bool at_apex = false;

void loop()
{
  raw_force = analogRead(force_sensor_pin);
  smoothed_force = (raw_force * 0.5) + (smoothed_force * 0.5);
  
  //Serial.println(smoothed_force);
  
  delta = smoothed_force - prev_force;
  if (delta > 0) {
    curr_increasing += 1;
  }
  else if (delta < 0) {
    curr_decreasing += 1;
  }
  
  pushed_delta = delta_list[pointer];
  if (pushed_delta > 0) {
    curr_increasing -= 1;
  }
  else if (pushed_delta < 0) {
    curr_decreasing -= 1;
  }
  
  //Serial.println(curr_decreasing);
  //Serial.println(curr_increasing);
  prev_force = smoothed_force;
  delta_list[pointer] = delta;
  pointer = (pointer + 1) % num_deltas; /* The pointer wraps
  around delta_list, hence making it act like a queue*/

  
  /* This next section checks if a certain number of deltas of 
  the past 20 are increasing/decreasing, and if so it powers on
  the corresponding LED, along with setting up the booleans
  for apex detection. This method is used to add another layer 
  of filtering to any noise that may be present */
  if (curr_increasing >= 15) { 
    digitalWrite(descending_pin, HIGH);
    digitalWrite(ascending_pin, LOW);
    ascending = false;
    descending = true;

  }
  else if (curr_decreasing >= 15) {
    digitalWrite(descending_pin, LOW);
    digitalWrite(ascending_pin, HIGH);
    ascending = true;
    descending = false;
  }
  else {
    digitalWrite(descending_pin, LOW);
    digitalWrite(ascending_pin, LOW);
    ascending = false;
    descending = false;
  }
  
  /* Here is the apex detection method, which is very simple. If
  the arduino was ascending, and no longer is, then it is 
  considered to be at its apex. Of course, once it starts descending,
  or ascending again, then it will no longer be at its apex. */
  if (was_ascending && !ascending) {
    at_apex = true;
    tone(piezo_pin, 750);
  }
  else if (at_apex && (ascending || descending)) {
    at_apex = false;
    noTone(piezo_pin);
  }

  /* In summary, this method is able to detect whether the arduino
  is ascending or descending within 0.2s along with having sufficient
  filters for noisy sensors. */
  
  was_ascending = ascending;
  delay(10); 
}
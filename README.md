# CalculateLuminosity

# Project Title

One Paragraph of project description goes here

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

What things you need to install the software and how to install them

```
Give examples
```

## Getting Started
   1) Login in the vocms061 machine and go in scratch0/Shifter_scripts/JSON.
   
      ```
      ssh cctrack@vocms061 -X
      cd scratch0/Shifter_scripts/JSON ```

   2) Here you find the script *computeLuminosity.sh*. To run over a given run range please submit two arguments: the =firstRun= and the =lastRun=; i.e. the first and last runs you certified during your shift.
   
     ```
      sh computeLuminosity.sh firstRun lastRun beamEnergy
     ```
     
      The =beamEnergy= argument is *optional* and should only be used when not in normal pp collision. In case of pA or HI collisions, please set this parameter to =HI=, which correspond to a beamEnergy of 4000 !GeV. If needed, one can set =beamEnergy= to any value (e.g. =2000=) if the beam conditions are not standard.
      
   4) To compute the luminosity for a given list of runs, produce a file containing a comma separated list of the runs in question and modify your call to computeLuminosity s.t. it reads 
   
     ```
      sh computeLuminosity.sh firstRun lastRun beamEnergy yourRunList.csv
     ```
     
   5) To get output in inverse femtobarns repleace beamEnergy above with "pp".  Note that firstRun and lastRun must contain the range of values filled in yourRunList.csv.

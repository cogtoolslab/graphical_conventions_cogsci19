# Recognition task

##### `/experiments/recog/`
- Input: Sketches from communication task and 3D objects
- Output: Sketch recognizability in context

### 1.2

##### stimuli from `graphical_conventions_sketches_scrambled40` collection

December 21, 2018

- What's different:
  - 1 recog experiment per refgame `gameID`
  - Each experiment has 40 trials (each repetition has 4 trials, each trial from a different refgame `gameID`)
  - Preserved temporal structure of repetitions

### 1.1

##### stimuli from `graphical_conventions_sketches_yoked` collection

December 21, 2018

- What's different:
  - 1 recog experiment per refgame `gameID`
  - Each experiment has 40 trials (all from the same refgame `gameID`)
  - Preserved temporal structure of trials

### 1.0

##### stimuli from `graphical_conventions_sketches_scrambled10` collection

November 20, 2018  

- What's different:
  - 4 recog experiments per refgame `gameID`
  - Each experiment has 10 trials (8 sketches from repeated condition, 2 from control condition with each sketch coming from a different refgame `gameID`)

# Communication task

#####  `/experiments/refgame/draw_chairs/`
- Input: Shapenet chair collection and experimental design
- Output: Human sketches and viewer decisions over time, communication efficiency timecourse

### 2.0

December 24, 2018

- What's new:
  - Added `useSubmitButton` flag in `game.core.js`
    - When set to `true`, the Sketcher must click the Submit button when they are done drawing for the Viewer to be able to see their drawing, so that the Viewer is not able to interrupt the Sketcher's drawing.
    - 30-second time limit in the speed bonus system still applies to the time taken since the Sketcher begins drawing until the Viewer selects an object 
  - Minimize context variability & increase sampling density within context: There are 8 versions of this experiment. Each of the chair categories: `['dining', 'waiting']` is evenly divided into two, fixed subsets: `['A','B']`. The assignment of ['repeated', 'control'] to each of the chair categories is randomized across pairs, and the repeated and control subsets are always from different chair categories. Thus approx. half of pairs will see dining repeatedly (with waiting items as control), and half of pairs will see waiting repeatedly (with dining as control). 

### 1.2

July 26, 2018

##### 1.2.0: `iterationName`s : `run3_size4_waiting`, `run4_generalization`

- What's new:
  - Context size changed back to 4
  - Two context generalization conditions (each has different `iterationName`)
    - In the within-cluster generalization condition (`run3_size4_waiting`): repeated and control objects are fetched from the same cluster
      - Use `waiting` flag in `game.core.js` to choose which cluster (waiting or dining) to fetch from for a game (when set to `true`, the waiting chairs cluster is used)
    - In the between-cluster generalization condition (`run4_generalization`): repeated and control objects are fetched from different clusters
    - Use `diffCats` flag in `game.core.js` to choose which condition (when set to `true`, between-cluster generalization condition is used)

### 1.1

July 20, 2018

##### 1.1.1 `iterationName` : `run2_chairs1k_size6`
##### 1.1.0 `iterationName` : `run2_chairs1k_size4`

- What's new:
  - Stimuli changed to chairs from ShapeNet
    - Clustered (PCA --> k-means) to increase similarity between objects in a context
  - Manipulated context size
    - **1.1.1**: context size = 6, num_reps = 6, num_rounds = 48
    - **1.1.0**: context size = 4, num_reps = 8, num_rounds = 40
  - Confirmation system
    - Viewer must confirm their choice of object after clicking on one (to prevent Viewer from hurriedly clicking on objects and achieving low accuracy)
  - Context color cues
    - Made context shift more perceptually salient using red and blue frames around repeated and control contexts (to make sure players know which context they are working in each trial)
  - Color-cued feedback sign
    - Shows how much bonus players got after each trial (to make trial-by-trial feedback more salient in addition to cumulative score display and bonusmeter)
  - Increased time limit
    - 30 seconds (to ensure Sketcher has enough time to draw as the task is more challenging with increased similarity within context and increased context size in 1.1.1)


### 1.0

June 30, 2018

##### 1.0.1 `iterationName` : `run1_chairsOnly` (Stimuli now restricted to chairs in the 'basic' 3D object dataset, before this point, files were under `/experiments/refgame/draw_basic/`)

##### 1.0.0 `iterationName` : `run0_bonusmeter`

- What's new:
  - Speed bonus system
    - Manipulates cost of drawing by imposing a 30-second time limit for each trial to incentivize efficient drawing.
    - Animated progress bar keeps track of additional bonus the players can receive depending on time taken for Viewer
      to make a correct guess. Additional bonus only given to correct guesses made under 30s (which should be more than enough for a Viewer to select an object based on the Sketcher's current sketch, but makes time cost more salient.)
    - All correct guesses receive a minimum bonus of $0.01. In the first 30s, the additional bonus players can receive       decreases from $0.03 to $0.00 -- in other words, the total bonus players an receive decreases from $0.04 to $0.01. Incorrect guesses do not receive a speed bonus, so the total bonus (accuracy bonus + speed bonus) is $0.00.
    - Two bonusmeter interfaces (progress bar and numerical feedback) were designed and the progress bar design was chosen

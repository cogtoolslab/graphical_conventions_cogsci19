### run2_chairs1k

We made a few substantial changes to the stimuli and design of this experiment:

    - Switched stimuli to chairs from ShapeNet to manipulate and increase similiarity between objects compared to previous stimuli
    - Manipulated context size: context size = 6 (6 reps, 48 rounds) and context size = 4 (8 reps, 40 rounds)
    - Implemented a confirmation system - the Viewer must confirm their choice of object after clicking on one. This is to prevent the Viewer from hurriedly clicking on objects and achieving lower accuracy.
    - Made context shift more perceptually salient using color cues - This is to make sure that the players know which context they are working in on each trial
    - Made trial-by-trial reward feedback more salient - in addition to the cumulative score display and bonus meter, we added a color-cued feedback sign that shows how much bonus the players got after each trial 
    - Increased time limit back to 30 seconds - Increased similarity (and context size) makes the task more challenging, so this is to ensure that the Sketcher has enough time to draw 


### "pilot2" --> iterationName in the mongodb is "run0_bonusmeter." 

Note: This experiment also used iterationName "run1_chairsOnly" when we ran this version with only the 3D chairs in the "basic" 3d object dataset.

June 3 2018

Implemented bonusmeter system. This manipulates cost of drawing by imposing time limit for each trial and therefore incentivizes efficient drawing (selectively sketching certain parts of an object to distinguish from other objects as early as possible in the drawing process).

The animated progress bar keeps track of the additional bonus the players can receive depending on the time taken for the Viewer to make a correct guess. The additional bonus is given to correct guesses made under 30s, which should be more than enough for a Viewer to select an object based on the Sketcher's current sketch, but makes the time cost more salient.

All correct guesses receive a minimum bonus of $0.01. In the first 30s, the additional bonus that players can receive decreases from $0.03 to $0.01 - in other words, the total bonus players can receive decrease from $0.04 to $0.01. Incorrect guesses receive a bonus of $0.00.

Otherwise design is identical to pilot1


### pilot1 [deprecated and part of different repo: hawkrobe/reference_games]

Aug 30 2017 [aka "pilot1"]

launch: Sep 20 2017

Implemented re-design of sketchpad_repeated.

Each pair now only sees objects from one of the categories (birds, chairs, cars, dogs), each containing 8 objects.

There are three phases to this experiment:
    - pre: All 8 objects sketched
    - repeating: A subset of 4 objects sketched 4 times each, mini-blocked.
    - post: All 8 objects sketched again

For a total of 8 + 16 + 8 = 32 trials total.

We want to counterbalance the category assignment across pairs.

Target pilot sample size: 4 * 5 = 20 pairs (matching sketchpad_basic size).


### pilot0 [deprecated and part of different repo: hawkrobe/reference_games]

May 31 2017 [aka "pilot0"; not saved to mongo due to ransomware thing]

"sketchpad_repeated" is a close variant of the "sketchpad" experiment.

There are four categories containing eight objects each. The categories are: birds, chairs, cars, dogs.

Objects were grouped into eight quartets: Four of these quartets contained objects from the same category ("close"); the other four of these quartets contained objects from different categories ("far").

On each trial, one quartet of objects shown. The sketcher's task was to make a sketch of the cued object such that the viewer could identify it from the quartet.

In this experiment, one of the "close" quartets will be presented 16 times, such that each object serves as the target four times across the session. One of the "far" quartets will also be repeated 16 times.

The remaining three "close" and three "far" quartets will be presented four times each, such that each object serves as the target at least once. Thus, these trials are identical to those in the original "sketchpad" experiment conducted in April 2017.

In other words, in addition to the "close" vs. "far" manipulation, we are also manipulating whether a quartet is "repeated" or presented only "once."

Total number of trials = 14 * 4 = 56

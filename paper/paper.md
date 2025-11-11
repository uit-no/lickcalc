---
title: 'lickcalc: Easy analysis of lick microstructure in experiments of rodent ingestive behaviour'
tags:
  - Python
  - feeding behaviour
  - neuroscience
  - hunger
  - thirst
authors:
  - name: K. Linnea Volcko
    orcid: 0000-0002-4234-0703
    affiliation: 1
  - name: James E. McCutcheon
    corresponding: true
    orcid: 0000-0002-6431-694X
    affiliation: 1
affiliations:
 - name: Dept. of Psychology, UiT The Arctic University of Norway, Tromsø, Norway
   index: 1
   ror: 00wge5k78
date: 15 October 2025
bibliography: paper.bib

---

# Summary

Lick microstructure is a term used to describe the information that can be obtained from a detailed study of when individual licks occur, when a rodent is drinking. Rather than simply recording total intake (volume consumed), lick microstructure examines how licks are grouped, and the spacing of these groups of licks. This type of analysis can provide important insight into why an animal is drinking, such as if it is driven by taste or as a response to the consequences of consumption (e.g. feeling “full” ). The simplcity of using `lickcalc`, requiring only a drag-and-drop of files, will make microstructural analysis accessible to any who wish to use it while providing sophisticated analyses with high scientific value.

# Statement of need

`lickcalc` is a software suite that performs microstructural lick analysis on data files containing timestamps of lick onset and offset, in MedAssociates or csv/txt format. In addition to providing an overview of individual files (corresponding to a particular session for a single subject), results of the analysis can be added to a table that is exportable to Excel.

Microstructural analysis was first described in @davis:1992 and has since then been used understand diverse phenomena. In-depth reviews on many of these, and microstructural parameters used to study them, are available [@johnson:2018; @naneix:2020; @smith:2001]. Briefly, although much of the foundational work on drinking microstruture was on licking for nutritive solutions (e.g., sucrose solutions), microstructural analysis can also be used to study intake of water [@mckay:2013; @santollo:2021], ethanol [@patwell:2021], and other tastants such as non-caloric artificial sweeteners, sodium and quinine [@lin:2012; @spector:1998; @verharen:2019]. Lick microstructure has been used to shed light on, for example, how licking is affected by neuropeptides [@mckay:2013], enzymes in the mouth [@chometton:2022], ovarian hormones [@santollo:2021], nutrient restriction [@naneix:2020], response to alcohol [@patwell:2021], and diet [@johnson:2012]. The number of lick bouts over a session are thought to reflect postingestive feedback from the consumed fluid, wheras the number of licks in a bout are thought to reflect palatability of the solution. 

Lick microstructure can provide a great deal of interesting information about why an animal is drinking. Often, changes in microstructure are accompanied by changes in total intake, but this is not always the case: sometimes, equal intake will be achieved by quite different licking patterns that indicate changes in orosensory and postingestive feedback [@johnson:2010; @volcko:2020]. Analyzing lick microstructure is therefore highly valuable in understanding how a manipulation affects appetite; if X causes an animal to feel more satiated after drinking, that may lead to a different interpretation than if X were to reduce the palatability of the solution. Because of the value of microstrucural data, many labs habitually record and analyze it. There are many others, however, that have not yet begun collecting these data. Investing in lickometers can be costly, but there are an increasing number of alternatives to commercial products such as those produced by Med Associates. Several open-source lickometer designs are now available (e.g. @frie:2024; @monfared:2024; @petersen:2024; @silva:2024; @raymond:2018). 

Recording individual licks with high temporal resolution is necessary for microstrucural analysis of drinking behavior, but another barrier to reporting microstructure is its analysis. This problem can now easily be solved by `lickcalc`. `lickcalc` does not require any special software or coding knowledge: all the user has to do is drag a file with timestamps of lick onset (and, ideally, offset) into the program and `lickcalc` will generate a detailed microstructural analysis, with a high degree of user control over key parameters. After loading a file and setting parameters, `lickcalc` displays results, the detail of which are an additional advantage of using the program. Tables show  values for number of licks, number of bursts, and burst size (among others) – the values that are often reported and used to draw inferences about postingestive and orosensory feedback of the solution. But imporantly, there are several charts displayed that show information that helps with quality control of the data and challenges the user to think critically about which parameters they have chosen. In short, `lickcalc` makes microstructural analysis accessible to any who have timestamps of lick onsets, while providing a lot of information on the data underlying the analysis which helps in choosing the appropriate parameters.  

# Key features

`lickcalc` has several features that make it exceptionally user-friendly at the same time as providing a sophisticated and detailed microstructural analysis. Some of these features include:

- **ease of use:** a file in Med Associates or CSV/TXT format simply needs to be dragged into the `lickcalc` software in order to perform the analyses. Parameters can be set manually using sliders, and results exported to Excel with the push of a button. 

- **flexibility:** the user sets key parameters appropriate for their experimental setup and data. Data can be examined by whole-session or different epochs.

- **customization:** by using the configuration file, users can change default settings to match their preferences and avoid manually changing settings for each file loaded.

- **results compilation:** data from multiple sessions and/or individuals can be exported into a single Excel file, wihch streamlines the analysis process. 

- **detail of analysis:** one of the benefits of using `lickcalc` is the level of detail it provides. In addition to the properties often reported (e.g. burst number, burst size), `lickcalc` computes and displays attributes of the data that are important in establishing the quality of the data and determining appropriate parameters for its microstructural analysis. Four charts are:
     1) *intraburst lick frequency,*  or how often certain interlick intervals within a burst of licking occur. While a rodent is licking, its tounge makes rythmic protrusions that are under the control of a central pattern generator [@travers:1997]. Rats typically lick 6-7 times per second [@davis:1992], while mice lick at a slightly higher rate [@johnson:2010]. In addition to these species differences, there are also strain differences [@johnson:2010; @stjohn2017]. Because intraburst lick rate is under the control of the central pattern generator, it should remain relatively stable across mice and conditions (unless a manipulation is expected to cause changes in the central pattern generator). A typical chart for a mouse might show a sharp peak around an intra-burst ILI of around 129, which corresponds to a lick rate of 7.75 Hz. Much smaller peaks are often present at the harmonics of the intra-burst ILI (e.g., a primary peak at 129 will have smaller peaks at 258, 387, and so on), often beause of “missed licks” in which the mouse attempts to lick but its toungue misses the spout. A large number of these, or other differences from the expected pattern of results, may indicate problems with the experimental setup (e.g. if the animal fails to reach the spout frequently, then perhaps the spout is too far away). 

     2) *lick length* is only available when lick offset is included in the data file. As with intraburst lick frequency, lick length should show little variability and the graph will have a sharp peak. Occasionally a lickometer will register longer licks than normal. This may be because a “lick” is registered by something other than a tounge, such as if a rodent grabs the spout with its paws, or if a fluid droplet hangs between the spout and the cage and is thus able to complete the electical circuit. Concerns about data quality may be warrented with increasing number and duration of long licks. `lickcalc` displays both the number and maximum duration (s) of licks above the threshold that the user has set. There is also an option to remove these problematic licks from the dataset. 

     3) *burst frequency,* or how often certain burst sizes occurred. This is informative because burst size, by virtue of being a mean (mean licks per burst), does not take into account potentially relevant information about the distribution of how many licks are in a burst. For example, a burst size of 80 could result from bursts all containing between 70 and 90 licks, or from many single licks and one or two burst with a lot of licks. The latter case might raise some questions about how reliable the burst size value is. Although single licks occur, they can also be caused by non-tounge contact with the lickometer. Changing the minimum licks/burst parameter can perhaps filter out some of these suspect “licks.”

     4) *Weibull probability*.  The Weibull analysis, as described in @davis:1996, uses a mathematical equation to fit the data to a survival function. Although used by some [@aja:2001; @moran:1998; @spector:1998], it is still relatively rare to find Weibull probabilities in microstructural analyses. The Weibull function can be used on several aspects of data, such as lick rate across a session, but in the `lickcalc` program the Weibull probability is calculated for burst size. It plots the probability that, given n licks, the mouse will continue to lick. This makes it sensitive to the number of licks per burst parameter that is set by the user. The Weibull alpha means…. And the Weibull beta means… 

# Design and usage

`lickcalc` is hosted by UiT The Arctic University of Norway and can be accessed at https://lickcalc.uit.no. Alternatively, it can be installed locally following instructions in the repository. To use `lickcalc`, the user drags in a file in Med Associates or CSV/TXT format and indicates which column contains the lick onsets and, if applicable, the lick offsets. A plot is automatically generated that displays a histogram of licks across the session. Session length defaults to the time of the last licks. This can be manually changed, or set in the optional "config file". Session length can be set in seconds, minutes, or hours. The bin size (licks per unit of time) can be changed manually or in the config file. The user can toggle between the default histogram and a plot showing cumulative licks. 

A microstructural analysis is, in essense, a division of individual licks into groups of licks. To perform this grouping, the user must set several parameters. One of these is the inter-lick interval (ILI), which is the minimum amount of time licks must be separated by in order to be considered separate groups. Early studies identified ILI of 251-500 ms as separating “bursts” of licking, and pauses of more than 500 ms as separating “clusters” of licking (i.e. a cluster of licks is made up of several bursts of licking). Others have argued that ILI of 1 s better reflects separation of lick bursts [@spector:1998]. In `lickcalc`, the user may set the ILI between 250 ms and 2 s. Another parameter that needs to be decided prior to the lick analysis is the minimum number of licks per burst. `lickcalc` allows between 1and 5 licks. The appropriate number of minimum licks/burst may vary depending on experimental set up, and the likelihood that a single lick respresents a lick rather than, for example, a tail touching the spout. Finally, in `lickcalc`, the user must set a “long-lick threshold” between 0.1 and 1 s. This parameter is only available when lick offset is included. Licks that are longer than the set threshold are counted as “long” and may indicate a problem (e.g. the mouse holding the spout with its paws) rather than a true lick. The user can decide whether to remove “long licks” or not. All of these parameters can be set manually or through the config file. Four plots are generated (see Key Features section above), and tables are displayed showing values of several properties: total licks, intraburst frequency, number of long licks, maximum duration of long likcs, number of bursts, mean licks per burst, weibull alpha, weibull beta, and weibull r-squared.

To save these data, the user has two options. The first is to export an excel file for the given data file. The user sets the animal ID and chooses which data should be exported in addition to the summary of the microstructural analysis. Data for "session histogram," "intraburst frequency," "lick length," "burst histogram," "burst probability," and "burst details" are available. These allow the user to recreate the plots displayed in `lickcalc`. The second option for saving the data is to add the microstructural data to "results summary" table in the app. The results in this table remain even as new data files are loaded, so the data from many sessions (and/or individual animals) can be exported into a single Excel file. In addition to the data from the whole session, the user can choose to divide the session into epochs, or to examine only the first n bursts, or perform a trial-based analysis (e.g., for Davis rig experiments). Each of these analysis epochs can be added to the results summary table. The table contains the data as well as the parameters (e.g., minimum burst size) used to generate them. Finally, a batch process feature is available allowing multiple files to be analysed using the same parameters.


# Acknowledgements

We acknowledge contributions from colleagues in the field of ingestive behaviour who have thought deeply about the meaning of patterns of licking. In particular, the following have either contributed data for us to test or have advised on the design of the program and analysis: (in alphabetical order) Derek Daniels, Samantha Fortin, Kevin Myers, Jess Santollo, Lindsey Schier, Alan Spector.

# References
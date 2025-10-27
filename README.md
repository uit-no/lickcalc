
# lickcalc

A simple app for performing analysis of lick microstructure in experiments of rodent ingestive behaviour.


## Installation

The application is hosted at https://en.uit.no/ansatte/james.e.mccutcheon

To install locally instead, the repository can be cloned, an environment made with the requirements.txt file, and the application can be run with

```
 python app.py
```
    
## Usage/Examples

Files can be opened by dragging into the interface. Various sliders allow parameters to be changed and associated calculations will be updated and figures will be replotted. The GUI is designed to be easy-to-use and self-explanatory but for fuller descriptions including citations to seminal experiments please see file.

### Custom Configuration

You can customize the default parameter values by uploading a custom configuration file:

1. Copy the `custom_config_example.yaml` file
2. Modify the values to your preferred defaults
3. Click the "Load Config File" button at the top of the app
4. Upload your custom config file

The custom configuration will override the default values and remain active until you click "Reset to Default" or reload the app.

Example custom config file:
```yaml
session:
  bin_size: 60
  fig_type: 'cumul'

microstructure:
  interburst_interval: 1.0
  min_licks_per_burst: 3
  long_lick_threshold: 0.5
```

Calculations are based on functions contained in the trompy package (link), particularly lickcalc and medfilereader. This packages can be installed separately with

pip install trompy

Core functions can also be extracted from this package and integrated with other code as required.


## Authors

- [@jaimemcc](https://www.github.com/jaimemcc)
- [@linneavolcko](https://www.github.com/linneavolcko)


## Acknowledgements

We would like to acknowledge all labs that have helped by contributing data and testing the application.


## Contributing and feedback

Contributions and feedback are always welcome! We welcome feedback, bug reports, and suggestions for new features.


## License

[GPL-3.0](https://choosealicense.com/licenses/gpl-3.0/)


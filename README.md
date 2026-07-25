

# lickcalc

A simple app for performing analysis of lick microstructure in experiments of rodent ingestive behaviour. The webapp is hosted for use by UiT The Arctic University of Norway at [lickcalc.uit.no](https://lickcalc.uit.no).

Earlier versions of this application can be found [here](https://github.com/jaimemcc/lickcalc_webapp) and [here](https://github.com/mccutcheonlab/Lick-Calc-GUI).

---

## Table of Contents

- [Installation](#installation)
- [System Requirements](#system-requirements)
- [Usage/Examples](#usageexamples)
- [Custom Configuration](#custom-configuration)
- [Core Functions](#core-functions)
- [Authors](#authors)
- [Citations](#citations)
- [Acknowledgements](#acknowledgements)
- [Contributing and Feedback](#contributing-and-feedback)
- [License](#license)




## Installation

The application is hosted at [lickcalc.uit.no](https://lickcalc.uit.no)

To install locally, clone the repository and create an environment using the `environment.yml` file. You can use either `conda` or `mamba`:

```powershell
# Using conda
git clone https://github.com/uit-no/lickcalc.git
cd lickcalc
conda env create -f environment.yml
conda activate lickcalc
python app.py
```

```powershell
# Using mamba (recommended for speed)
git clone https://github.com/uit-no/lickcalc.git
cd lickcalc
mamba env create -f environment.yml
mamba activate lickcalc
python app.py
```
The app will then be available by opening a browser and typing `localhost:8050` in the address bar.

## System Requirements (for local install)

- Python 3.8 or newer
- Windows, macOS, or Linux
- Conda or Mamba (recommended)



## Usage/Examples

Files can be opened by dragging into the interface. Various sliders allow parameters to be changed, calculations will update, and figures will be replotted. The GUI is designed to be easy-to-use and self-explanatory. For full documentation and citations to seminal experiments, see [lickcalc.uit.no/help](https://lickcalc.uit.no/help).




### Custom Configuration

You can customize the default parameter values by uploading a custom configuration file:

1. Copy the `custom_config_example.yaml` file
2. Modify the values to your preferred defaults
3. Click the "Load Config File" button at the top of the app
4. Upload your custom config file

The custom configuration will override the default values and remain active until you reload the app.

Quick config keys reference:

| Section | Key | Allowed Values | Example |
|---|---|---|---|
| session | fig_type | hist, cumul | hist |
| microstructure | first_n_ilis | integer 1-20 | 5 |
| plots | intraburst_fig_type | intraburst_ili, first_n_ili | first_n_ili |
| plots | longlick_fig_type | lick_lengths, intercontact_lengths | intercontact_lengths |
| plots | bursthist_fig_type | burst_hist | burst_hist |
| plots | burstprob_fig_type | weibull_prob | weibull_prob |

See full configuration details in [docs/CONFIG_README.md](docs/CONFIG_README.md).



### Core Functions
Calculations are based on functions contained in the [trompy](https://github.com/mccutcheonlab/trompy) package, particularly `lickcalc` and `medfilereader`. These packages can be installed separately with:

```powershell
pip install trompy
```

Core functions can also be extracted from this package and integrated with other code as required.




## Authors

- [@jaimemcc](https://www.github.com/jaimemcc)
- [@linneavolcko](https://www.github.com/linneavolcko)




## Citations
If you use `lickcalc` in your work, please cite us as follows:

Volcko KL & McCutcheon JE (2026). lickcalc: Easy analysis of lick microstructure in experiments of rodent ingestive behaviour. *bioRxiv*, https://doi.org/10.64898/2026.03.09.710511

**BibTeX:**
```bibtex
@article{lickcalc,
	author = {Volcko, K. Linnea and McCutcheon, James E.},
	title = {lickcalc: Easy analysis of lick microstructure in experiments of rodent ingestive behaviour},
	journal = {bioRxiv},
	year = {2026},
	doi = {10.64898/2026.03.09.710511},
	url = {https://doi.org/10.64898/2026.03.09.710511}
}
```



## Acknowledgements

We would like to acknowledge all labs that have helped by contributing data and testing the application.




## Contributing and Feedback

Contributions and feedback are always welcome! Please see our [issues page](https://github.com/uit-no/lickcalc/issues) for bug reports and feature suggestions.




## License

[GPL-3.0](https://choosealicense.com/licenses/gpl-3.0/)

This project is licensed under the GNU General Public License v3.0. You are free to use, modify, and distribute this software, but any derivative work must also be open source under the same license.


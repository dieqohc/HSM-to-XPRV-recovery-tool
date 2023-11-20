# HSM_Secret to XPRV tool

This is a tool created in order to help those in the hard situation of having funds locked (on-chain) after the failure of [core-lightning](https://github.com/ElementsProject/lightning), specially addressed but not limited to those having problems with c-lightning on the [Umbrel]() software.

## Installation

Just download the as a .zip and place it where you want, unpack it and opening the folder where everything is decompressed run the following command to install the dependencies:

⚠**WARNING**: In order to avoid the dependencies breaking any of your system packages, it is advised to work within a Virtual environment instance of your preference. 

```bash
pip install - r requirements.txt
```

## Usage

1. Within the recovery file you can change and specify the route to the *'hsm_secret'* file, by default it is in the same directory and there is an exception in the .gitignore file in order to avoid leaks. (make sure to always check twice.)

2. Simply open a terminal or the file within vscode, and run the recovery.py in an instant you will have your xprv and xpub printed to screen along with a small warning like this.

```
XPRV: xprv9abcjdldlkjdflksdfvlksdfv122...
XPUB: xpub6sdvclsdkvfsdv87875tpoijsc09...

When importing the XPRV the derivation path for the funds is "m/*" which can be represented as "m/0.
```

The xprv can be imported on Sparrow wallet in order to have control and availability of your funds. 
- This can be achieved by going to *File>New Wallet>(Give name to wallet)>New or Imported Software Wallet>Master Private Key (BIP32)*

It is recommended to move your funds out to a safe wallet once you get this information as once displayed as there is no warranty of no trace or history after the the data is displayed on the terminal.

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

## License

The license for this project is GNU GPLv3

To learn more about the permissions, conditions and limitations of this license go here: [GNU General Public License v3.0](https://choosealicense.com/licenses/gpl-3.0/)
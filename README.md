# fix_IdoA_charmmgui

Set of scripts used to fix the wrong conformation of Iduronic Acid sulfated at position 2 (IdoA-2S) generated by default by charmm-gui.

The procedure is as follows :

    1. The position of H2 and O2 is inverted by flipping the coordinates
    2. A short minimization MD is run with all atoms from the IdoA-containing molecule restrained, except for those in the 2 Sulfate.
    3. The minimization relaxes the position of the 2 sulfate and brings it closer to the O2, rendering the correct configuration of IdoA.

A combination of python, bash and gromacs is used, and all the scripts in this repository are meant to be used together.
All files should be kept in the same folder upon downloading.
The fix_IdoA_charmmgui.sh wrapper script handles all the others, and it is meant to be used directly. 

Example usage:

```bash
./fix_IdoA_charmmgui.sh -c $fol/wrong.gro -i $fol/mol.itp -p $fol/topol.top -r $fol/restr_invert_S.itp -o $fol/01-correct
```

Where $fol is the target folder where all the simulation files are stored:

    -$fol/wrong.gro - gro file with wrong configuration, as gotten from charmm-gui (often called step3_input.gro). It can be the full system as well as the IdoA0containing molecule alone.
    -$fol/mol.itp - itp file for the IdoA-containing molecule, as gotten from charmm-gui (often, CARB.itp).
    -p $fol/topol.top - system topology as gotten from charmm-gui (often, topol.top).
    -r $fol/restr_invert_S.itp - output name for the restrain file used for the simulation. Any name would work here.
    -o $fol/01-correct - output name for the simulation results.

Please kindly report any mistakes, or additional needed functionalities.
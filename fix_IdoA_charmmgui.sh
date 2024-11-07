#!/bin/bash

# Wrapper code for generating the right starting point for a molecule with IdoA-2S as generating from charmm-gui (produces the wrong conformation) 
# All the files in this repository must be kept in the same folder for it to work!

# Help message
usage() {
    echo "Usage: $0 [-c <input_gro>] [-i <input_itp>] [-r <output_restraint>] [-o <output_prefix>] [-p <topol_file>]"
    echo "  -c  Input .gro file with incorrect configuration (default: './wrong.gro')"
    echo "  -i  Input .itp molecule topology (default: './mol.itp')"
    echo "  -p  System topology file (default: './topol.top')" 
    echo "  -r  Output restraint file after inversion (default: './restr_invert_S.itp')"
    echo "  -o  Output prefix for generated files (default: './01-correct')"
    echo "  -h  Show this help message"
}

# Parse command-line arguments
while getopts ":c:i:p:r:o:h" opt; do
    case $opt in
        c) wrong_gro="$OPTARG" ;;
        i) mol_itp="$OPTARG" ;;
        r) out_restr="$OPTARG" ;;
        o) output_prefix="$OPTARG" ;;
        p) topol="$OPTARG" ;;
        h) usage; exit 0 ;;
        \?) echo "Invalid option: -$OPTARG" >&2; usage; exit 1 ;;
    esac
done

# Set default values if not provided by user
wrong_gro="${wrong_gro:-./wrong.gro}"
out_restr="${out_restr:-./restr_invert_S.itp}"
output_prefix="${output_prefix:-./01-correct}"
topol="${topol:-./topol.top}"
mol_itp="${mol_itp:-./mol.itp}"

# Rest of the script
echo 
echo "------- Running with the following parameters: --------"
echo "Input .gro file: $wrong_gro"
echo "Input .itp file: $mol_itp"
echo "System topology file: $topol"
echo "Output restraint file: $out_restr"
echo "Output prefix: $output_prefix"
echo "-------------------------------------------------------"
echo 

#### SCRIPT STARTS HERE ####
# Check if GROMACS and Python are available
if ! command -v gmx &> /dev/null; then
    echo "GROMACS (gmx) is required but not installed. Aborting."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Aborting."
    exit 1
fi

# Prepare index and restraint files using GROMACS commands
mol_atom_len=$(python3 find_mol_len.py $mol_itp) #Calculates length of the molecule to restrain
sel="a 1-$mol_atom_len" # makes a selection that goes from atom 1 to len of the molecule (it doesn't matter if it does not select the right molecule, the important is that the length = mol_len)
sel2=$(echo "$sel" | sed 's/ /_/') #for further selections

#Gen the resntrain file
printf "$sel\nq\n" | gmx make_ndx -f "$wrong_gro" -o index_invert.ndx
printf "$sel2\n" | gmx genrestr -f "$wrong_gro" -o restr.itp -fc 5000 5000 5000 -n index_invert.ndx
rm -f index_invert.ndx

# Execute Python script for IDOA inversion
echo "-----------------------EXECUTING PYTHON SCRIPT---------------------------------"
python3 invert_idoa.py "$wrong_gro" correct.gro restr.itp "$out_restr" "$mol_itp"
echo "-------------------------------------------------------------------------------"

# Run minimization
echo "-----------------------RUNNING MD MINIMIZATION---------------------------------"
gmx grompp -f 0-rotateC2.mdp -c correct.gro -o ${output_prefix}.tpr -po ${output_prefix}-mdout.mdp -r correct.gro -p $topol -maxwarn 1
gmx mdrun -v -deffnm ${output_prefix}
echo "-------------------------------------------------------------------------------"

# Notify user of completion
if [ -f "$output_prefix.gro" ]; then
echo "Inversion and restraint update complete. Files are ready for further simulation steps."
echo "Use ${output_prefix}* for continuation"
else
echo "The process was not completed succesfully, check errors above"
fi

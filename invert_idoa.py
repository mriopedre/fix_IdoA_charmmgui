#%%
import sys

# Check if the correct number of arguments was passed
if len(sys.argv) != 6:
    print("Usage: python invert_aidoa.py <input_gro> <output_gro> <input_restr> <output_restr> <mol_itp>")
    sys.exit(1)

input_gro = sys.argv[1]
output_gro = sys.argv[2]
input_restr = sys.argv[3]
output_restr = sys.argv[4]
mol_itp = sys.argv[5]

class AidoaC2Inverter:
    """This class is used to invert the configuration of the C2 AIDOA in a .gro file.
    The C2 AIDOA is inverted by switching the coordinates of the H2 and O2 atoms.
    The inversion should be followed by a minimization with restraints to ensure proper geometry of the sulfated AIDOA.

    This is an answer to the usolved problem in charmm-gui, which produces IdoA-2S with the wrong C2 configuration.
    """

    def flip_coordinates(self, line1, line2):
        """Switch the x, y, z coordinates of two atoms in a .gro file line."""
        line1_tokens = line1.split()
        line2_tokens = line2.split()
        
        # Swap coordinates
        line1_tokens[3:6], line2_tokens[3:6] = line2_tokens[3:6], line1_tokens[3:6]

        # Format based on atom name length
        if len(line1_tokens[1]) >= 7 or len(line2_tokens[1]) >= 7:
            return self._format_long_line(line1_tokens), self._format_long_line(line2_tokens)
        else:
            return self._format_standard_line(line1_tokens), self._format_standard_line(line2_tokens)

    def _format_standard_line(self, tokens):
        """Format a line for .gro files with standard atom name lengths."""
        return f"{tokens[0]:>10}{tokens[1]:>5}{tokens[2]:>5}{tokens[3]:>8}{tokens[4]:>8}{tokens[5]:>8}\n"

    def _format_long_line(self, tokens):
        """Format a line for .gro files with longer atom numbers that merge with atom names."""
        return f"{tokens[0]:>10}{tokens[1]:>10}{tokens[2]:>8}{tokens[3]:>8}{tokens[4]:>8}\n"

    def _is_aidoa_s2_sulfated(self, lines, index):
        """Check if lines match the AIDOA configuration with H2 and O2 next to S2."""
        return ('AIDOA' in lines[index] and 'H2' in lines[index] and 
                'O2' in lines[index + 1] and 'S2' in lines[index + 2]
                and 'AIDOA' in lines[index + 2])

    def _is_o2_s2_aidoa_check(self, lines, index, modified_line_idx):
        """Ensure O2 is the sulfated line when found."""
        return ('AIDOA' in lines[index] and 'O2' in lines[index] and 
                'S2' in lines[index + 1] and index == modified_line_idx)

    def invert_aidoa_c2_configuration(self, input_filename, output_filename):
        """Modify .gro file lines to invert AIDOA configuration."""
        
        with open(f"{input_filename}") as input_file:
            lines = input_file.readlines()

        with open(f"{output_filename}", 'w') as output_file:
            modified_line_idx = -1

            for i, line in enumerate(lines):
                if self._is_aidoa_s2_sulfated(lines, i):
                    #Check if AidoA is sulfated in S2.
                    line1, line2 = self.flip_coordinates(lines[i], lines[i + 1])
                    output_file.write(line1)
                    modified_line_idx = i + 1

                elif self._is_o2_s2_aidoa_check(lines, i, modified_line_idx):
                    #Extra (in principle unnecessary) check to make sure the O2 is the one that is sulfated
                    #This could be in the upper if, but it is separated in case some topology had something different
                    output_file.write(line2)
                    modified_line_idx = -1
                else:
                    output_file.write(line)
        print(f"{input_filename} configuration inverted and saved to {output_filename}")

# This for editing the restraint file

class AidoaRestraintModifier:
    """This class is used to identify and unrestrain atoms in a GROMACS restraint file based on specified conditions."""

    def identify_unrestrained_atoms(self, gro_filename):
        """Identify atoms that should not be restrained based on specified conditions in a .gro file.
        The conditions are being part of the S2 sulfated AIDOA group (S2, OS22, OS23, OS24). i.e having S2 in name.
        Returns a list with the atom numbers that shoul not be restrained.
        """
        not_restrain = []

        with open(gro_filename) as file:
            lines = file.readlines()

            for line in lines:
                # Add atoms to not_restrain if line contains 'AIDOA' and 'S2'
                if 'AIDOA' in line and 'S2' in line:
                    not_restrain.append(line.split()[2])  # Capture atom number
    
        return not_restrain

    def unrestrain_atoms(self, gro_filename, restraint_filename, output_filename):
        """Update restraint file to unrestrain atoms based on the identified target atoms.
        """
        unrestrained_atoms = self.identify_unrestrained_atoms(gro_filename)

        with open(restraint_filename) as file:
            lines = file.readlines()

        with open(output_filename, 'w') as output_file:
            for index, line in enumerate(lines):
                # Copy header lines as-is
                if index < 4:
                    output_file.write(line)
                else:
                    atom_id = line.split()[0]
                    # Add comment to lines corresponding to unrestrained atoms
                    if atom_id in unrestrained_atoms:
                        output_file.write(f";{line}")
                    else:
                        output_file.write(line)

        print(f"Restraint file updated and saved to {output_filename}")

    def add_restraint_to_itp(self, itp_filename, restraint_file):
        """Add restraints to an .itp file.
        It adds the lines so the restraints can be used if defineds in the mdp file.
        """
        with open(itp_filename, 'r') as itp_file:
            lines = itp_file.readlines()
                
        with open(itp_filename, 'w') as itp_file:

            for line in lines:
                if line.startswith("#ifdef ROTATE_C2"):
                    break
                itp_file.write(line)

            itp_file.write("#ifdef ROTATE_C2\n")
            itp_file.write(f'#include "{restraint_file}"\n')
            itp_file.write('#endif\n')

        print(f"Restraints added to {itp_filename}")


# Instantiate the classes and run inversion and restraint update
inverter = AidoaC2Inverter()
inverter.invert_aidoa_c2_configuration(input_gro, output_gro)

modifier = AidoaRestraintModifier()
modifier.unrestrain_atoms(output_gro, input_restr, output_restr)

modifier.add_restraint_to_itp(mol_itp, output_restr)
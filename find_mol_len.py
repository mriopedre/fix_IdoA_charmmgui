#%%
class FindMolItpLen():
    """Find the number of atoms in a molecule from a .itp file.
    Usefull to generate the appropriate restraints for a molecule."""

    def find_mol_len(self, itp_file):
        """Find the number of atoms in a molecule from a .itp file."""
        with open(itp_file, 'r') as itp_file:
            lines = itp_file.readlines()
            for line in lines:
                line_tokes = line.split()
                if "bonds" in line_tokes:
                    break
                if len(line_tokes) >= 8 and line_tokes[0].isdigit():
                    mol_len = line_tokes[0]
        return int(mol_len)
    
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python find_mol_len.py <itp_file>")
        sys.exit(1)

    itp_file = sys.argv[1]
    finder = FindMolItpLen()
    print(finder.find_mol_len(itp_file))

import mmap
import sys

"""
A very crude parser for SDDS files (produced by OPAL simulation runs).

The parser does not check if the SDDS file is valid. Result files can be
large, therefore we map the file to memory preventing reading everything. The
user can get values at fixed dump steps (get()) or at specific positions [m]
with getAtSpos.
"""
class SddsParser:

    def __init__(self, filename):
        self.columns = {}
        self.params = {}
        self.data_pos = []
        self.sdds_data_mem = 0
        self.data_start = 0

        self.memoryMapFile(filename)
        self.parseHeader()


    def __del__(self):
        self.sdds_data_mem.close()


    def get(self, name, position = -2):
        self.sdds_data_mem.seek(self.data_pos[position])

        line = self.sdds_data_mem.readline().decode("utf-8")
        column_idx = self.columns[name]
        return float(line.split("\t")[column_idx])


    def getColumn(self, name):
        column = []
        for i in range(0, len(self.data_pos) - 1):
            column.append(self.get(name, i))
        return column


    def findClosestDumps(self, name, position_m):
        spos_before  = 0
        value_before = 0
        spos_after   = 0
        value_after  = 0

        for i in range(0, len(self.columns) - 1):
            cursor_pos = self.get('s', i)

            if position_m < cursor_pos:
                index_before = max(0, i-1)
                value_before = self.get(name, index_before)
                value_after  = self.get(name, i)
                spos_before  = self.get('s', index_before)
                spos_after   = cursor_pos
                return ( (spos_before, value_before),
                         (spos_after, value_after) )

        raise LookupError("Specified position (" + position_m + ") never \
                           reached by simulation")


    def getAtSpos(self, name, position_m):
        (before, after) = self.findClosestDumps(name, position_m)

        # simple linear interpolation
        interpolated_value = 0.0
        interpolated_value = before[1]
        if position_m - before[0] > 1e-8:
            interpolated_value += (position_m - before[1]) * \
                    (after[1] - before[1]) / (after[0] - before[0])

        return interpolated_value


    def memoryMapFile(self, filename):
        try:
            f = open(filename, "r+")
        except IOError:
            print('Cannot open SDDS file ' + filename)
        else:
            self.sdds_data_mem = mmap.mmap(f.fileno(), 0)


    def parseHeader(self):

        column_idx = 0
        param_idx = 0

        # file starts with 'SDDS1'
        line = self.sdds_data_mem.readline()
        line = self.sdds_data_mem.readline()
        while(line):

            line = line.decode("utf-8")

            if line.startswith("&description"):
                # strange linebreak in sdds description
                line = self.sdds_data_mem.readline()

            elif line.startswith("&parameter"):
                param_name = line.split(",")[0]
                param_name = param_name.split("name=")[1]
                self.params[param_name] = param_idx
                param_idx += 1

            elif line.startswith("&column"):
                column_name = line.split(",")[0]
                column_name = column_name.split("name=")[1]
                self.columns[column_name] = column_idx
                column_idx += 1

            elif line.startswith("&data"):
                self.sdds_data_mem.readline()
                self.sdds_data_mem.readline()
                self.data_start = self.sdds_data_mem.tell()
                break

            else:
                raise Exception("Invalid syntax in SDDS header")

            line = self.sdds_data_mem.readline()

        self.data_pos.append(self.sdds_data_mem.tell())
        line = self.sdds_data_mem.readline()
        while(line):
            self.data_pos.append(self.sdds_data_mem.tell())
            line = self.sdds_data_mem.readline()


# test
if __name__ == "__main__":
    parser = SddsParser(sys.argv[1])

    print("E = " + str(parser.get("energy")))
    print("E = " + str(parser.getAtSpos("energy", 1.0e-7)))

from mmio.ex9055dm import EX9055DM


class ControlBoard(EX9055DM):
    def __init__(self, address):
        EX9055DM.__init__(self, address)
        self.issues = {
          'Pumpensumpf': 0,
          'Rückstauklappe Hausmeister': 1,
          'Rückstauklappe Technikraum': 2,
          'Rauchmelder Allgemein B10': 3,
          'Rauchmelder Allgemein L06': 4,
          'Rauchmelder Allgemein L08': 5,
          'Hitzemelder Tiefgarage': 6,
          'Gasheizung': 7
        }

    def check_issues(self):
        found_issues = []
        for k, v in self.issues.items():
            input_status = self.read_input(v)
            if input_status:
                if input_status is 1:
                    found_issues.append(k)
            else:
                raise ValueError('Could not read from the device')

        return found_issues

    def set_led(self, color):
        if color is 'green':
            self.write_output(0, 1)
        elif color is 'red':
            self.write_output(1, 1)

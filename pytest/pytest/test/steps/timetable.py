from datetime import datetime, date, timedelta, time

class TimeTableSegment:

    def __init__(self, start_time: str, num_days: int, calendar: list):
        self.start_time = datetime.strptime(start_time, '%d-%m-%Y %H:%M:%S')
        self.num_days = num_days
        if len(calendar) != num_days:
            raise Exception('Length of Calendar does not match number of days!')
        self.calendar = calendar

    @classmethod
    def from_start_and_end_date(
            cls,
            first_day: date, last_day: date,
            morning_start_time: time, days_off: list):

        calendar_days = [first_day + timedelta(days=x) for x in range(0, (last_day-first_day).days + 1)]

        i = 1
        calendar = []
        for day in calendar_days:
            if day.weekday() == 5 or day.weekday() == 6 or (day in days_off):
                todays_operation = ['Off', 'Off']
            else:
                todays_operation = ['On', 'On']
            calendar.append(todays_operation)

#        return 'cc'
        return cls(
            start_time='{} {}'.format(first_day.strftime("%d-%m-%Y"), morning_start_time.strftime("%X")),
            num_days=len(calendar),
            calendar=calendar
        )

    def as_hex_string(self):
        hex_str = '{:08X}'.format(int(self.start_time.timestamp()))
        hex_str += ' {:02X}'.format(self.num_days)

        calendar_array = []
        calendar_byte = 0

        for i in range(self.num_days):

            x = 0x0
            if self.calendar[i][0] == 'On':
                x |= 0x1
            if self.calendar[i][1] == 'On':
                x |= 0x2

            if i % 4 == 0:
                if i > 0:
                    calendar_array.insert(0, calendar_byte)
                calendar_byte = x
            else:
                calendar_byte = calendar_byte + (x << (2 * (i % 4)))

        calendar_array.insert(0, calendar_byte)

        for b in calendar_array:
            hex_str += ' {:02X}'.format(b)

        return hex_str


class TimeTable:

    def __init__(self):
        pass


def make_time_table(num_segments: int,):
    pass


if __name__ == '__main__':
#    tts = TimeTableSegment(
#        '28-04-2020 10:00:00', 3,
#        [['On', 'On'], ['On', 'On'], ['On', 'On']]
#    )
#    print('Timetable as hex: {}'.format(tts.as_hex_string()))
#
#    tts = TimeTableSegment(
#        '28-04-2020 10:00:00', 3,
#        [['On', 'On'], ['Off', 'Off'], ['On', 'On']]
#    )
#    print('Timetable as hex: {}'.format(tts.as_hex_string()))
#
#    tts = TimeTableSegment(
#        '28-04-2020 10:00:00', 5,
#        [['On', 'On'], ['On', 'On'], ['On', 'On'], ['On', 'On'], ['On', 'On']]
#    )
#    print('Timetable as hex: {}'.format(tts.as_hex_string()))

    # tts = TimeTableSegment(
    #     '05-10-2020 08:30:00', 255,
    #     ([['On', 'On'], ['On', 'On'], ['On', 'On'], ['On', 'On'], ['On', 'On'], ['Off', 'Off'], ['Off', 'Off']] * 37)[:255]
    # )
    # print('Timetable as hex: {}'.format(tts.as_hex_string()))

    print('Reference Full Year Timetable 2020')

    # Realistic Example
    # 29th Jan - 24th Mar 2020
    #   Public Holidays (during school term):
    #        9th Mar: Labour day
    # 15th Apr - 26th Jun 2020
    #   Public Holidays (during school term):
    #       25th Apr: ANZAC day
    #        8th Jun: Queens Birthday
    # 13th Jul - 18th Sep 2020
    #   Public Holidays (during school term)
    #       None
    # 5th Oct - 18th Dec 2020
    #   Public Holidays (during school term)
    #       23rd Oct: Grand Final Friday
    #        3rd Nov: Melbourne Cup
    tts1 = TimeTableSegment.from_start_and_end_date(
        date(2020, 1 , 29), date(2020, 3, 24),
        time(hour=8, minute=30),
        [
            date(2020, 3, 9)    # Labour Day
        ]
    )
    print('Timetable Segment 1 as hex: {}'.format(tts1.as_hex_string()))

    tts2 = TimeTableSegment.from_start_and_end_date(
        date(2020, 4 , 15), date(2020, 6, 26),
        time(hour=8, minute=30),
        [
            date(2020, 4, 25),    # ANZAC Day
            date(2020, 6, 8)      # Queens Birthday
        ]
    )
    print('Timetable Segment 2 as hex: {}'.format(tts2.as_hex_string()))

    tts3 = TimeTableSegment.from_start_and_end_date(
        date(2020, 7 , 13), date(2020, 9, 18),
        time(hour=8, minute=30),
        []
    )
    print('Timetable Segment 3 as hex: {}'.format(tts3.as_hex_string()))

    tts4 = TimeTableSegment.from_start_and_end_date(
        date(2020, 10 , 5), date(2020, 12, 18),
        time(hour=8, minute=30),
        [
            date(2020, 10, 23),    # Grand Final Friday
            date(2020, 11, 3)       # Melbourne Cup
        ]
    )
    print('Timetable Segment 4 as hex: {}'.format(tts4.as_hex_string()))

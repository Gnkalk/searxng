import datetime
import os
def write(TypeWrite, grouping="", number=""):
    # opening a file in write or append mode based on the 'TypeWrite' parameter
    with open("searx/statistics.log", TypeWrite) as log_file:
            # get the current date and time in "YYYY-MM-DD" format
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
            # create a string log entry with the timestamp, number of results and grouping
            log_entry = f"{timestamp} | Number of results: {number} | Grouping: {grouping}\n"
            log_file.write(log_entry)

def log_statistics(grouping, number):
    try:
        # try to append the statistics to the log file
        write("a", grouping, number)
    except FileNotFoundError:
        # if the file does not exist, create it and write the statistics
        write("w", grouping, number)

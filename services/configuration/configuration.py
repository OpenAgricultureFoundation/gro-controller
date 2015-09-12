import time


class SerialParameters:
    baud_rate = 9600
    serial_read_timeout = 0.01  # seconds
    establish_connection_timeout = 4  # seconds
    receive_message_timeout = 3  # seconds


class ManualProfiler:
    """ Class to profile a function

    To profile a function/loop/any code, create an instance of ManualProfiler outside of it.
    Then, at the top of the code to be profiled, call instance.startLoop to start the path and add the first point
    every time you call instance.addPoint within the code, the profiler will store the time delta from the last point
    at the end, call endLoop to indicate the end of the code path
    ManualProfiler will automatically break up the profiling into different code paths so that you can see how long
    each segment of each path took.
    Unfortunately, this means that code with lots of points inside of conditional statements will have lots of different
    run types ( <= 2^n, where n is the number of points inside conditionals, to be exact).
    Whenever you want to get the current profiling stats, call instance.getStatusList.
    This will return a list with each line of the status output. ex. Use "\n".join(instance.getStatusList())
    Calling getStatusList WILL NOT clear the stats, you need to call clear for that! So if you want
    pseudo-continuous stats: every once in a while, call getStatusList and then clear. Or for a bucketed approach,
    call clear only every x times of calling getStatusList.

    NOTE: ManualProfile will only store self.max_runs_per_type of each run to prevent stats calculation from taking
    too long. It will still have the latest results tho, see the endLoop method.
    Change max_runs_per_type this if you want data for more runs and don't mind the time cost.

    NOTE: If you getStatus and want to clear within the same loop, you can call endLoop AFTER clear so that you
    don't clear the run you just profiled

    """
    initial_sample_name = 'start'     # name of the first sample, ex 'start'
    final_sample_name = 'end'       # name of the end sample, ex 'end'
    max_runs_per_type = 200         # limit to x runs so that stats don't take too long to compute
    runs_to_remove_after_max = 10   # used when we get more than max_runs_per_type of a run_type. see endLoop
    max_name_length = 50            # For fixed width printing, will trim names to this size

    def __init__(self):
        # Not cleared (see self.clear())
        self._code_paths_tree = {self.initial_sample_name: {}}  # code paths tree, always starts with the first sample.
        self._last_created_run_type = 0                 # For each new run_type, increment this and use the new val
        self._run_length_dictby_run_type = {}           # dict (by run_type) of length of run for that type
        self._names_list_dictby_run_type = {}           # dict (by run_type) of (list of names) for that type

        # Cleared (see self.clear())
        self._run_times_dictby_run_type = {}            # dict (by run_type) of list of runs for that type

        # Loop stuff
        self._loop_start_time = None
        self._last_sample_time = None
        self._last_sample_name = None
        self._current_path = None                       # stores where we are in the code path
        self._current_run_timedelta_list = None         # stores the times for the current run
        self._current_run_names_list = None             # stores names for current run to add to self._names_list...

    def _clearLoopRelated(self):
        """Clear all loop related attributes, called at the end of a loop"""
        for item in [self._last_sample_name, self._last_sample_time, self._loop_start_time,
                     self._current_path, self._current_run_timedelta_list, ]:
            item = None

    def clear(self):
        """Clears all the runs from this class so we can get new data

        Note: this does not clear the run types in the _code_paths_tree, we want them to be consistent across runs
        """
        self._clearLoopRelated()

        self._run_times_dictby_run_type = {}

    def startLoop(self):
        """Call this at the start of the loop to start the benchmarking"""

        self._loop_start_time = time.time()

        assert self.initial_sample_name in self._code_paths_tree

        # code_paths_tree should have the first sample in it by default
        self._current_path = self._code_paths_tree[self.initial_sample_name]
        self._current_run_names_list = [self.initial_sample_name]
        self._current_run_timedelta_list = [0]              # start should always be 0

        self._last_sample_name = self.initial_sample_name
        self._last_sample_time = self._loop_start_time

    def addPoint(self, name: str):
        """Call this every time you want add a time sample"""
        assert self._loop_start_time is not None, "loop_start_time should be set before calling addPoint! see startLoop"
        assert self._current_path is not None, "current_path should not be None! see startLoop, endLoop"

        # get times
        curtime = time.time()
        time_delta = curtime - self._last_sample_time
        self._last_sample_time = curtime

        # timedelta and names list
        self._current_run_timedelta_list.append(time_delta)
        self._current_run_names_list.append(name)

        # Code path
        if name not in self._current_path:      # If the name is not in the current_path, this is a new path!
            self._current_path[name] = {}           # continue the tree for this code path
        self._current_path = self._current_path[name]

        # record name just in case...
        self._last_sample_name = name

    def endLoop(self):
        """Call this at the end of loop to end benchmarking. Will record total loop time as well"""
        assert self._current_run_timedelta_list is not None

        # store total time as final_sample_name
        curtime = time.time()
        self._current_run_timedelta_list.append(curtime - self._loop_start_time)
        self._current_run_names_list.append(self.final_sample_name)

        # if we are on a new path, create a new run type
        if self.final_sample_name not in self._current_path:     # NEW path (no final_sample_name in leaf node)
            self._last_created_run_type += 1                            # increment
            run_type = self._last_created_run_type                      # and use it
            self._current_path[self.final_sample_name] = run_type       # store the run type

            self._run_length_dictby_run_type[run_type] = len(self._current_run_timedelta_list)
            self._names_list_dictby_run_type[run_type] = self._current_run_names_list
            # will init cleared lists in the next if block, we need to do it for existing paths sometimes too

        run_type = self._current_path[self.final_sample_name]       # Get the run type

        # if we haven't encountered this path since we've cleared, need to init lists
        if run_type not in self._run_times_dictby_run_type:
            # init run_times, run_count
            self._run_times_dictby_run_type[run_type] = []

        # if there are already the max amount of this run type, trim by self.runs_to_remove_after_max
        if len(self._run_times_dictby_run_type[run_type]) >= self.max_runs_per_type:
            self._run_times_dictby_run_type[run_type] = \
                self._run_times_dictby_run_type[run_type][self.runs_to_remove_after_max:]

            # have run_type, store all the info related to this run
            # make sure this list is the right length. all runs of a specific type should be same
        assert len(self._current_run_timedelta_list) == self._run_length_dictby_run_type[run_type]
        # create lists for this run_type if they don't exist yet (they are cleared but code paths aren't!
        self._run_times_dictby_run_type[run_type].append(self._current_run_timedelta_list)

    def getStatusList(self):

        status_list = ['-----Profiling-----']
        # we already know they are all the same length since we check that when we start
        for run_type in sorted(self._run_times_dictby_run_type.keys()):
            status_list.append("Run type %d, count %d" % (run_type, len(self._run_times_dictby_run_type[run_type])))
            names_list = self._names_list_dictby_run_type[run_type]

            timedelta_listby_sample = list(zip(*self._run_times_dictby_run_type[run_type]))       # NOTE dat star magic.
            max_list = [max(x) for x in timedelta_listby_sample]
            avg_list = [sum(x)/len(x) for x in timedelta_listby_sample]  # NOTE python3 style division, will fail in py2

            assert len(max_list) == len(avg_list) == len(names_list)

            for name, avg_val, max_val in zip(names_list, avg_list, max_list):
                status_list.append("%*.*s:  %2.2f  %2.2f" % (self.max_name_length, self.max_name_length,
                                                             name, avg_val, max_val))

        return status_list

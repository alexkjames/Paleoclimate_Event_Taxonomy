### Instructions to create a taxonomy entry

1. Create LiPD file for original record containing the event.
    a. Make sure to store the data in paleo table 0 measurement table 0.
    b. All columns in the LiPD file should have a variable name and variable unit name.
    c. LiPD file should also contain lat+lon information, archive type, and original publication info (at least the DOI)

2. Create the taxonomy entry from the LiPD file
    a. Use the example given in the Example Workflow notebook
    b. Entry should be saved to appropriate folder in taxonomy before being pushed to Github

3. Taxonomy entry structure:

    - LiPD file containing all variables from that record (Depth, age, dependent variable(s) are required)

	- Entries for individual events contained within one of the dependent variables

		- Basic event stats (start, end)

		- Event type (if applicable, otherwise enter as "misc")

		- Which variable and variable index the event is associated with (if a record has 							   
			both D18O and D13C, the associated variable index/name should be stored
			inside the individual event entry)

		- Different idealized versions of the same event

			- Idealized event stats (spline timings and amplitudes)

## required drivers changes:
moved to design doc: https://docs.google.com/document/d/1aXcOWI5Lnx0vsXjr_a6Vivs_aSetklWdbz6khamyB00/edit?usp=sharing

## todos / notes
- it might seem funny that I check the command/reply are strings, but I think we probably need to do it that way where drivers serialize them to extJSON strings before assertion time, so we can test truncation works as required. 
-  we should test serverConnectionId is present on 4.2+, and not present < 4.2. I skipped this because Rust doesn't expose that yet. need to add
 -  should test serviceId is included when in load balancer mode
* for drivers w/ operationIds, add a test that is included when appropriate

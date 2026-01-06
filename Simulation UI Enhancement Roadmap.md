# Simulation UI Enhancement Roadmap

## DISCLAIMER: How to use this ROADMAP: READ THIS EVERY TIME
ONLY WORK BY PHASE - Do not race ahead and execute multiple phases at once - work through each phase, and stop the moment you finish each one. When you stop a phase, provide the user with a list of manual checks to ensure the phase was completed successfully. You can also pitch a couple automatic checks you can execute to the user, but ensure these checks do not interfere with the code you have created, and also ensure that the checks are valid, and actually test what you are aiming to test. Also make sure you only run these tests when the user provides direct permission.

## Phase 1: Add Wrap and Diagonals Toggle to UI

### Backend Changes
1. Update [simulator.html](cci:7://file:///Users/ronitbhandari/Desktop/Simulator/flask_app/templates/simulator.html:0:0-0:0) template:
   - Add checkboxes for "Enable Wrapping" and "Use Diagonals" in the Initial Conditions section
   - Set default values (wrapping off, diagonals on to match current behavior)
   - Add appropriate CSS classes for styling

2. Update [simulator_client.js](cci:7://file:///Users/ronitbhandari/Desktop/Simulator/flask_app/static/js/simulator_client.js:0:0-0:0):
   - Add event listeners for the new toggles
   - Include these values in the simulation start payload
   - Update the form submission handler to collect these values

3. Update [simulator_manager.py](cci:7://file:///Users/ronitbhandari/Desktop/Simulator/flask_app/simulator_manager.py:0:0-0:0):
   - Modify [run_simulation](cci:1://file:///Users/ronitbhandari/Desktop/Simulator/flask_app/simulator_manager.py:142:4-284:81) to pass wrap/diagonals to `update_grid`
   - Ensure proper type conversion for these parameters

### Verification Steps
**Manual Checks:**
1. Load the simulator and verify the new toggles appear in the Initial Conditions section
2. Start a simulation and verify the toggles affect the simulation:
   - With wrapping on, heat/ripples should appear on opposite sides
   - With diagonals off, propagation should be only orthogonal
3. Check browser console for any JavaScript errors

**Automated Checks (require permission):**
- Unit test for form submission with different toggle combinations
- Verify parameter passing in test simulation runs

## Phase 2: Add Parameter Descriptions with Info Tooltips

### Backend Changes
1. Update the simulator configuration to include parameter descriptions
2. Modify [simulator.html](cci:7://file:///Users/ronitbhandari/Desktop/Simulator/flask_app/templates/simulator.html:0:0-0:0):
   - Add info icons (ℹ️) next to each parameter
   - Include hidden description divs
   - Add CSS for tooltip styling and behavior

2. Update [simulator_client.js](cci:7://file:///Users/ronitbhandari/Desktop/Simulator/flask_app/static/js/simulator_client.js:0:0-0:0):
   - Add event listeners for info icon clicks
   - Implement tooltip show/hide functionality
   - Handle click-outside to dismiss tooltips

3. Add CSS for tooltips:
   - Position relative to info icons
   - Smooth transitions
   - Responsive design

### Verification Steps
**Manual Checks:**
1. Hover over info icons to verify tooltips appear
2. Check tooltip positioning on different screen sizes
3. Verify tooltips contain the correct descriptions
4. Test clicking outside closes tooltips
5. Verify no JavaScript errors in console

**Automated Checks (require permission):**
- Test tooltip visibility toggle
- Verify tooltip content matches config

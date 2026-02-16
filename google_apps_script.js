/**
 * CONFIGURATION
 * ========================================================
 */
const CALENDAR_ID = "257def119740d55b7172773ef6a0b8432132819762e5bf7b294d156fbd71647a@group.calendar.google.com"; // Voleibol Bunyola
const JSON_URL = "https://raw.githubusercontent.com/LlucValdes/calendario-voleibol/main/matches.json";
const TEAMMATES = [
  "YOUR_EMAIL_HERE@gmail.com",
  // "teammate2@example.com",
  // "teammate3@example.com"
];

/**
 * MAIN FUNCTION - Run this manually or set up a daily trigger.
 */
function syncMatches() {
  const matches = fetchMatches();
  if (!matches || matches.length === 0) {
    Logger.log("No matches found or error fetching.");
    return;
  }

  const calendar = CalendarApp.getCalendarById(CALENDAR_ID);
  if (!calendar) {
    Logger.log("❌ Calendar not found: " + CALENDAR_ID);
    return;
  }

  Logger.log(`Found ${matches.length} matches in JSON.`);

  // Get future events to avoid duplicates
  const now = new Date();
  const futureEvents = calendar.getEvents(now, new Date(now.getTime() + (365 * 24 * 60 * 60 * 1000)));

  // Map simplified existing events key -> event object
  const existingMap = {};
  futureEvents.forEach(evt => {
    // We use a tag if possible, or fall back to title + time
    const uid = evt.getTag("internal_uid");
    if (uid) {
      existingMap[uid] = evt;
    }
  });

  matches.forEach(match => {
    const uid = match.uid;
    const existingEvent = existingMap[uid];

    // Parse Date
    let startTime, endTime;
    if (match.all_day) {
      startTime = new Date(match.begin);
      endTime = new Date(match.begin); // All day events need just date usually, but for API createAllDayEvent takes date
    } else {
      startTime = new Date(match.begin); // ISO string handles timezone
      endTime = new Date(startTime.getTime() + (2 * 60 * 60 * 1000)); // +2 hours
    }

    // Skip old matches
    if (endTime < now) return;

    if (existingEvent) {
      // UPDATE
      // We can update title, description, location if they changed
      // For simplicity, we just log it exists. 
      // Un-comment lines below to force updates if you need
      // existingEvent.setLocation(match.location);
      // existingEvent.setDescription(match.description);
      Logger.log(`Skipping existing: ${match.name}`);
    } else {
      // CREATE
      Logger.log(`✨ Creating: ${match.name}`);
      let newEvent;

      const options = {
        description: match.description,
        location: match.location,
        guests: TEAMMATES.join(","), // THIS SENDS INVITES
        sendInvites: true
      };

      if (match.all_day) {
        newEvent = calendar.createAllDayEvent(match.name, startTime, options);
      } else {
        newEvent = calendar.createEvent(match.name, startTime, endTime, options);
      }

      // Save UID tag so we don't duplicate it next time
      newEvent.setTag("internal_uid", uid);
    }
  });
}

function fetchMatches() {
  try {
    const response = UrlFetchApp.fetch(JSON_URL);
    const json = response.getContentText();
    return JSON.parse(json);
  } catch (e) {
    Logger.log("Error fetching JSON: " + e);
    return [];
  }
}

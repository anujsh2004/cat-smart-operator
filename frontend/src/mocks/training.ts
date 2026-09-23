// Generated from backend/app/db/seed_training.json so mock mode shows the real modules and quizzes.
import type { Module, Quiz } from "@/api/types";

export const mockModules: Module[] = [
  {
    "content_url": null,
    "trigger_anomaly_type": "seatbelt_unfastened",
    "module_id": "TM01",
    "title": "Seatbelt & Cab Safety",
    "category": "safety",
    "format": "video",
    "duration_min": 8,
    "description": "Why the seatbelt matters in a rollover or tip-over, correct cab entry and exit with three points of contact, and the pre-start cab checklist."
  },
  {
    "content_url": null,
    "trigger_anomaly_type": "proximity_hazard",
    "module_id": "TM02",
    "title": "Working Near People",
    "category": "safety",
    "format": "simulation",
    "duration_min": 15,
    "description": "Interactive scenarios on exclusion zones, blind spots, swing radius and communicating with ground crew before moving."
  },
  {
    "content_url": null,
    "trigger_anomaly_type": "excessive_idling",
    "module_id": "TM03",
    "title": "Fuel-Efficient Operation",
    "category": "efficiency",
    "format": "video",
    "duration_min": 12,
    "description": "Cut idle time and fuel burn: auto-idle and engine shutdown, the right power mode for each task, and planning cycles to avoid waiting."
  },
  {
    "content_url": null,
    "trigger_anomaly_type": "abnormal_cycle_time",
    "module_id": "TM04",
    "title": "Smooth Cycle Technique",
    "category": "technique",
    "format": "simulation",
    "duration_min": 15,
    "description": "Practise combined boom, stick and swing movements, optimal truck positioning and swing angles for shorter, smoother cycles."
  },
  {
    "content_url": null,
    "trigger_anomaly_type": "unsafe_operation",
    "module_id": "TM05",
    "title": "Incident Response Basics",
    "category": "incident_response",
    "format": "quiz",
    "duration_min": 10,
    "description": "What to do in the first minutes after a near miss or incident: make safe, report, preserve the scene and record details."
  },
  {
    "content_url": null,
    "trigger_anomaly_type": null,
    "module_id": "TM06",
    "title": "Wet-Weather Operation",
    "category": "safety",
    "format": "quiz",
    "duration_min": 10,
    "description": "Operating on wet or muddy ground: traction, slope stability, reduced visibility and adjusting speed and loads."
  },
  {
    "content_url": null,
    "trigger_anomaly_type": null,
    "module_id": "TM07",
    "title": "Trenching Best Practice",
    "category": "technique",
    "format": "video",
    "duration_min": 14,
    "description": "Digging accurate trenches: checking for buried services, spoil placement, depth control and working safely beside open trenches."
  },
  {
    "content_url": null,
    "trigger_anomaly_type": null,
    "module_id": "TM08",
    "title": "Book an Instructor Session",
    "category": "technique",
    "format": "instructor",
    "duration_min": 60,
    "description": "One-to-one coaching with a certified instructor in the machine, focused on the areas your recent sessions highlight."
  }
];

export const mockQuizzes: Record<string, Quiz> = {
  "TM01": {
    "questions": [
      {
        "id": "q1",
        "prompt": "When should the seatbelt be fastened?",
        "options": [
          "Only when travelling on public roads",
          "Before starting the engine and whenever the machine is running",
          "Only on slopes steeper than 15 degrees",
          "Only when carrying a full bucket"
        ],
        "answer_index": 1,
        "explanation": "The seatbelt keeps you inside the ROPS cab if the machine tips or rolls. It must be on whenever the engine is running."
      },
      {
        "id": "q2",
        "prompt": "What is the safest way to climb into the cab?",
        "options": [
          "Jump up using the track as a step",
          "Use the steering levers as handholds",
          "Keep three points of contact on the handrails and steps",
          "Carry your tools in one hand while climbing"
        ],
        "answer_index": 2,
        "explanation": "Three points of contact (two hands and a foot, or two feet and a hand) prevents most slips and falls when mounting a machine."
      },
      {
        "id": "q3",
        "prompt": "If the machine starts to tip over, you should:",
        "options": [
          "Jump out of the cab immediately",
          "Stay belted in, hold on and brace yourself",
          "Open the door to prepare to exit",
          "Lower the boom as fast as possible and climb out"
        ],
        "answer_index": 1,
        "explanation": "Jumping out puts you in the crush zone. Stay belted inside the protective cab and brace yourself."
      }
    ]
  },
  "TM02": {
    "questions": [
      {
        "id": "q1",
        "prompt": "A worker walks into your swing radius. What do you do first?",
        "options": [
          "Finish the current cycle quickly",
          "Stop all movement and sound the horn",
          "Swing away from them slowly",
          "Wave them out while continuing to dig"
        ],
        "answer_index": 1,
        "explanation": "Stop all movement first. Resume only when the person has left the exclusion zone and you have eye contact or a signal."
      },
      {
        "id": "q2",
        "prompt": "What is the minimum exclusion zone around an operating excavator?",
        "options": [
          "1 m from the tracks",
          "The full swing radius plus a safety margin",
          "Only the area in front of the bucket",
          "No zone is needed if the horn is working"
        ],
        "answer_index": 1,
        "explanation": "Anyone within the swing radius can be struck by the counterweight or attachment. Keep the whole radius plus a margin clear."
      },
      {
        "id": "q3",
        "prompt": "Before reversing or tracking you should:",
        "options": [
          "Rely on the reverse alarm alone",
          "Check mirrors and cameras and confirm the path is clear",
          "Raise the bucket high for visibility",
          "Increase engine speed to move quickly past people"
        ],
        "answer_index": 1,
        "explanation": "Alarms are easy to tune out. Always check mirrors and cameras, and use a spotter if visibility is limited."
      },
      {
        "id": "q4",
        "prompt": "How should you communicate with a spotter?",
        "options": [
          "Agree hand signals before work starts",
          "Shout over the engine noise",
          "Flash the work lights",
          "Use whatever signals seem obvious at the time"
        ],
        "answer_index": 0,
        "explanation": "Agreed signals (or radios) before starting avoid misunderstandings when it matters."
      }
    ]
  },
  "TM03": {
    "questions": [
      {
        "id": "q1",
        "prompt": "You expect to wait 10 minutes for a truck. What is the best practice?",
        "options": [
          "Leave the engine at high idle",
          "Shut down or let auto-shutdown engage",
          "Keep swinging the empty bucket",
          "Rev the engine to keep hydraulics warm"
        ],
        "answer_index": 1,
        "explanation": "An idling excavator still burns several litres per hour. For waits longer than a few minutes, shut down or rely on auto-shutdown."
      },
      {
        "id": "q2",
        "prompt": "Which power mode suits light grading work?",
        "options": [
          "Maximum power mode",
          "An economy/smart mode",
          "It makes no difference",
          "Travel mode"
        ],
        "answer_index": 1,
        "explanation": "Economy modes lower engine speed when full power isn't needed, cutting fuel use with little loss of productivity."
      },
      {
        "id": "q3",
        "prompt": "Roughly what share of engine hours is idle on a typical site?",
        "options": [
          "Under 5%",
          "About 30-40%",
          "Over 80%",
          "Exactly 50%"
        ],
        "answer_index": 1,
        "explanation": "Telematics studies commonly show 30-40% idle time, which is why reducing it is the quickest fuel saving."
      }
    ]
  },
  "TM04": {
    "questions": [
      {
        "id": "q1",
        "prompt": "What is the ideal swing angle between digging and dumping?",
        "options": [
          "180 degrees",
          "About 30-45 degrees",
          "90 degrees exactly",
          "Swing angle doesn't affect cycle time"
        ],
        "answer_index": 1,
        "explanation": "Positioning trucks so the swing is 30-45 degrees keeps cycles short and reduces fuel use."
      },
      {
        "id": "q2",
        "prompt": "Smooth cycles come from:",
        "options": [
          "Moving one control at a time",
          "Blending boom, stick and swing movements",
          "Always using maximum engine speed",
          "Slamming the bucket to empty it"
        ],
        "answer_index": 1,
        "explanation": "Combining movements overlaps the stages of the cycle, which is where experienced operators save seconds."
      },
      {
        "id": "q3",
        "prompt": "Your cycle time is much longer than usual. A likely cause is:",
        "options": [
          "The bucket is too full",
          "Poor truck or pile positioning",
          "The seatbelt is fastened",
          "Sunny weather"
        ],
        "answer_index": 1,
        "explanation": "Bad positioning adds swing and travel to every cycle. Re-plan the setup before speeding up the controls."
      }
    ]
  },
  "TM05": {
    "questions": [
      {
        "id": "q1",
        "prompt": "After a near miss with a pedestrian, your first step is:",
        "options": [
          "Carry on and report at the end of the shift",
          "Stop, make the machine safe and check the person is unharmed",
          "Move the machine away from the area",
          "Call your family"
        ],
        "answer_index": 1,
        "explanation": "Make the machine safe (bucket down, controls locked) and check on people before anything else."
      },
      {
        "id": "q2",
        "prompt": "Why report near misses that caused no harm?",
        "options": [
          "They don't need reporting",
          "They reveal hazards before someone gets hurt",
          "Only to meet paperwork quotas",
          "To assign blame"
        ],
        "answer_index": 1,
        "explanation": "Near misses are free lessons. Reporting them lets the site fix the hazard before it causes an injury."
      },
      {
        "id": "q3",
        "prompt": "Which detail matters most in an incident report?",
        "options": [
          "The weather forecast for tomorrow",
          "Time, location, people involved and what happened",
          "Your opinion of who was at fault",
          "The machine's paint colour"
        ],
        "answer_index": 1,
        "explanation": "Accurate facts (when, where, who, what) are what investigators need."
      }
    ]
  },
  "TM06": {
    "questions": [
      {
        "id": "q1",
        "prompt": "On wet ground you should:",
        "options": [
          "Travel faster to avoid getting stuck",
          "Reduce speed and avoid sharp turns",
          "Carry heavier loads for stability",
          "Work closer to trench edges"
        ],
        "answer_index": 1,
        "explanation": "Traction drops sharply on wet ground. Slow down and avoid sudden turns or braking."
      },
      {
        "id": "q2",
        "prompt": "Rain makes trench walls and embankments:",
        "options": [
          "More stable",
          "Less stable and more likely to collapse",
          "Unaffected",
          "Easier to dig with no risk"
        ],
        "answer_index": 1,
        "explanation": "Water adds weight and reduces soil cohesion. Keep the machine back from edges after rain."
      },
      {
        "id": "q3",
        "prompt": "In fog or heavy rain, visibility is poor. What helps most?",
        "options": [
          "Turning the radio up",
          "Work lights, a spotter and slower movements",
          "Opening the cab door",
          "Relying on memory of the site layout"
        ],
        "answer_index": 1,
        "explanation": "Improve visibility, use a spotter and slow down so there is time to react."
      }
    ]
  },
  "TM07": {
    "questions": [
      {
        "id": "q1",
        "prompt": "Before digging a trench you must:",
        "options": [
          "Start at the deepest point",
          "Check service drawings and locate buried utilities",
          "Remove the bucket teeth",
          "Dig as fast as possible to beat the rain"
        ],
        "answer_index": 1,
        "explanation": "Striking gas, power or water lines is a major hazard. Always locate services first."
      },
      {
        "id": "q2",
        "prompt": "Where should spoil be placed?",
        "options": [
          "Right at the trench edge",
          "At least 1 m back from the edge",
          "Inside the trench",
          "On the access road"
        ],
        "answer_index": 1,
        "explanation": "Spoil at the edge adds load and can fall back in. Keep it set back from the edge."
      },
      {
        "id": "q3",
        "prompt": "How do you keep a consistent trench depth?",
        "options": [
          "Guess by eye",
          "Use grade control or check with a laser or level regularly",
          "Dig until the bucket is full",
          "Only check at the end"
        ],
        "answer_index": 1,
        "explanation": "Regular checks or machine grade control avoid over-digging and rework."
      }
    ]
  },
  "TM08": {
    "questions": [
      {
        "id": "q1",
        "prompt": "What is the best way to prepare for an instructor session?",
        "options": [
          "Come with no expectations",
          "Review your recent alerts and pick 1-2 skills to improve",
          "Only attend if something went wrong",
          "Bring your own machine"
        ],
        "answer_index": 1,
        "explanation": "Using your recent alerts and insights makes the session focused and useful."
      },
      {
        "id": "q2",
        "prompt": "During coaching the instructor will mostly:",
        "options": [
          "Operate the machine while you watch",
          "Observe you operating and give live feedback",
          "Give a written exam",
          "Service the machine"
        ],
        "answer_index": 1,
        "explanation": "Hands-on practice with live feedback is the fastest way to build skill."
      },
      {
        "id": "q3",
        "prompt": "After the session you should:",
        "options": [
          "Forget about it",
          "Practise the techniques and track your metrics",
          "Book another session immediately",
          "Change machines"
        ],
        "answer_index": 1,
        "explanation": "Your dashboard metrics show whether the new techniques are working."
      }
    ]
  }
};

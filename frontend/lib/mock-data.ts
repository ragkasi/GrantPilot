import type { Organization, Project, AnalysisResult } from "@/types";

export const mockOrganization: Organization = {
  id: "org_brightpath",
  name: "BrightPath Youth Foundation",
  mission:
    "Provide after-school STEM mentoring and academic support to low-income middle school students in Columbus, Ohio.",
  location: "Columbus, Ohio",
  nonprofit_type: "501(c)(3)",
  annual_budget: 420000,
  population_served: "Low-income middle school students (grades 6–8)",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

export const mockProject: Project = {
  id: "proj_stem_2026",
  organization_id: "org_brightpath",
  grant_name: "Community STEM Access Fund",
  grant_source_url: null,
  funder_name: "Ohio Community Foundation",
  grant_amount: "$50,000 – $150,000",
  deadline: "May 15, 2026",
  status: "analyzed",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

export const mockAnalysis: AnalysisResult = {
  project_id: "proj_stem_2026",
  eligibility_score: 82,
  readiness_score: 74,

  requirements: [
    {
      id: "req_1",
      text: "Applicant must be a registered 501(c)(3) nonprofit.",
      type: "eligibility",
      importance: "required",
      status: "satisfied",
      confidence: 0.95,
      evidence: [
        {
          document_name: "Mission Statement.pdf",
          page_number: 1,
          summary:
            "Organization identifies as a 501(c)(3) nonprofit incorporated in Ohio.",
        },
      ],
    },
    {
      id: "req_2",
      text: "Programs must focus on STEM education or mentoring for youth.",
      type: "eligibility",
      importance: "required",
      status: "satisfied",
      confidence: 0.93,
      evidence: [
        {
          document_name: "Program Description.pdf",
          page_number: 1,
          summary:
            "Core programs include STEM mentoring, coding workshops, and academic tutoring.",
        },
        {
          document_name: "Annual Report.pdf",
          page_number: 4,
          summary:
            "2024 programs reached 312 students through STEM workshops and mentoring.",
        },
      ],
    },
    {
      id: "req_3",
      text: "Applicant must serve low-income youth in Ohio.",
      type: "eligibility",
      importance: "required",
      status: "satisfied",
      confidence: 0.91,
      evidence: [
        {
          document_name: "Program Description.pdf",
          page_number: 2,
          summary:
            "Programs exclusively serve Title I schools in Columbus with over 80% free/reduced lunch eligibility.",
        },
      ],
    },
    {
      id: "req_4",
      text: "Applicant must provide proof of IRS tax-exempt status.",
      type: "required_document",
      importance: "required",
      status: "not_satisfied",
      confidence: 0,
      evidence: [],
    },
    {
      id: "req_5",
      text: "Organization must have been operational for at least 2 years.",
      type: "eligibility",
      importance: "required",
      status: "satisfied",
      confidence: 0.88,
      evidence: [
        {
          document_name: "Mission Statement.pdf",
          page_number: 1,
          summary:
            "Founded in 2019. Organization has been operating for over 5 years.",
        },
      ],
    },
    {
      id: "req_6",
      text: "Applicant must submit a current list of board members.",
      type: "required_document",
      importance: "required",
      status: "not_satisfied",
      confidence: 0,
      evidence: [],
    },
    {
      id: "req_7",
      text: "Grant request must not exceed 25% of annual operating budget.",
      type: "budget",
      importance: "required",
      status: "satisfied",
      confidence: 0.9,
      evidence: [
        {
          document_name: "Annual Budget.pdf",
          page_number: 1,
          summary:
            "Annual operating budget is $420,000. Maximum 25% = $105,000, within grant range.",
        },
      ],
    },
    {
      id: "req_8",
      text: "Applicant must demonstrate matching funds of at least 10% of grant request.",
      type: "budget",
      importance: "required",
      status: "partially_satisfied",
      confidence: 0.4,
      evidence: [
        {
          document_name: "Annual Budget.pdf",
          page_number: 2,
          summary:
            "Budget mentions in-kind contributions from school district, but no cash match commitment letter was found.",
        },
      ],
    },
    {
      id: "req_9",
      text: "Programs must serve students in grades 6–8.",
      type: "eligibility",
      importance: "required",
      status: "satisfied",
      confidence: 0.94,
      evidence: [
        {
          document_name: "Program Description.pdf",
          page_number: 1,
          summary:
            "All programs target middle school students in grades 6 through 8.",
        },
      ],
    },
    {
      id: "req_10",
      text: "Organization must provide a detailed program budget for grant funds.",
      type: "narrative",
      importance: "required",
      status: "partially_satisfied",
      confidence: 0.62,
      evidence: [
        {
          document_name: "Annual Budget.pdf",
          page_number: 3,
          summary:
            "Organizational budget provided. Program-specific line items for grant activities are not fully broken out.",
        },
      ],
    },
  ],

  missing_documents: [
    {
      name: "IRS Determination Letter",
      required: true,
      description:
        "Official IRS letter confirming 501(c)(3) tax-exempt status. Required for eligibility verification.",
    },
    {
      name: "Board of Directors List",
      required: true,
      description:
        "Current list of board members with roles and contact information. Required by most Ohio foundations.",
    },
    {
      name: "Matching Funds Commitment Letter",
      required: false,
      description:
        "Letter confirming a matching funds commitment of at least 10% of the grant request (~$5,000–$15,000).",
    },
  ],

  risk_flags: [
    {
      severity: "high",
      title: "IRS determination letter not uploaded",
      description:
        "This is a hard eligibility requirement. Without it, the application will be disqualified before review.",
    },
    {
      severity: "high",
      title: "Matching funds not documented",
      description:
        "The grant requires a 10% cash match. In-kind contributions alone may not satisfy this requirement. Upload a commitment letter.",
    },
    {
      severity: "medium",
      title: "Program budget not itemized",
      description:
        "An organizational budget was uploaded, but grant-specific line items are missing. Add a program budget before submitting.",
    },
    {
      severity: "medium",
      title: "Board list not provided",
      description:
        "Most Ohio funders require a current board member list. Upload it to avoid a documentation deficiency.",
    },
  ],

  draft_answers: [
    {
      id: "draft_1",
      question:
        "Describe your organization's mission and the primary programs you operate.",
      draft_answer:
        "BrightPath Youth Foundation is a 501(c)(3) nonprofit organization based in Columbus, Ohio, dedicated to providing after-school STEM mentoring and academic support to low-income middle school students. Our core programs include weekly STEM workshops, one-on-one coding mentorship, and academic tutoring for students in grades 6–8 attending Title I schools.\n\nIn 2024, we served 312 students across four Columbus partner schools, achieving a 91% program completion rate and a measurable improvement in math assessment scores among 74% of participants.",
      citations: [
        {
          document_name: "Mission Statement.pdf",
          page_number: 1,
          summary: "States mission, founding year, and 501(c)(3) status.",
        },
        {
          document_name: "Program Description.pdf",
          page_number: 1,
          summary:
            "Describes STEM workshops, coding mentorship, and tutoring programs.",
        },
        {
          document_name: "Annual Report.pdf",
          page_number: 4,
          summary:
            "Reports 312 students served in 2024 with 91% completion rate.",
        },
      ],
      missing_evidence: [],
      confidence: 0.91,
    },
    {
      id: "draft_2",
      question:
        "How does your program specifically serve low-income youth in Ohio, and what is your evidence of need?",
      draft_answer:
        "BrightPath exclusively partners with Title I middle schools in Columbus, Ohio, where more than 80% of students qualify for free or reduced-price lunch. Our target population faces significant gaps in access to quality STEM programming outside of school hours.\n\nAccording to our 2024 Annual Report, 78% of students we served had no prior access to organized STEM activities before joining BrightPath. Our program description references Columbus City Schools data confirming that our partner schools rank in the bottom quartile for STEM outcomes in Ohio.",
      citations: [
        {
          document_name: "Program Description.pdf",
          page_number: 2,
          summary:
            "Describes Title I school partnerships and 80%+ free/reduced lunch rate.",
        },
        {
          document_name: "Annual Report.pdf",
          page_number: 6,
          summary: "78% of students had no prior STEM program access.",
        },
      ],
      missing_evidence: [],
      confidence: 0.87,
    },
    {
      id: "draft_3",
      question:
        "What specific outcomes will this grant support, and how will you measure success?",
      draft_answer:
        "This grant will support expansion of our STEM mentoring program to two additional Columbus partner schools, adding capacity to serve approximately 120 new students annually.\n\nSuccess will be measured through: (1) student participation rates and program completion, tracked via attendance records; (2) pre/post STEM interest and confidence surveys; and (3) academic performance in math and science, tracked in partnership with schools.\n\nNote: Specific outcome targets for the new expansion sites are not yet documented in uploaded materials. We recommend adding projected outcomes and measurable milestones to your program description before final submission.",
      citations: [
        {
          document_name: "Program Description.pdf",
          page_number: 3,
          summary:
            "Describes current outcomes tracking methodology for existing programs.",
        },
        {
          document_name: "Annual Report.pdf",
          page_number: 5,
          summary:
            "Reports outcomes methodology and 2024 performance benchmarks.",
        },
      ],
      missing_evidence: [
        "Specific outcome targets and measurable projections for new program expansion sites are not documented in the uploaded materials.",
      ],
      confidence: 0.72,
    },
  ],
};

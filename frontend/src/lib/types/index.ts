export interface User {
	legacy_user_id: number;
	name: string;
	role: 'student' | 'facilitator';
}

// LoginResponse.active_courses item — no cohort/category (backend limitation)
export interface CourseInfo {
	legacy_course_id: number;
	name: string;
}

export interface LoginResponse {
	access_token: string;
	token_type: string;
	legacy_user_id: number;
	name: string;
	role: 'student' | 'facilitator';
	active_courses: CourseInfo[];
}

// GET /facilitator/courses response item
export interface Course {
	legacy_course_id: number;
	legacy_user_group_id: number | null;
	name: string;
	cohort: string;
	category: string;
	is_active: boolean;
	is_favorite: boolean;
}

export interface Student {
	legacy_user_id: number;
	name: string;
	is_active: boolean;
}

// GET /facilitator/courses/{id}/quests, GET /facilitator/quests/{id}
export interface Quest {
	id: string;
	cached_course_id: number;
	quest_number: number;
	quest_type: 'sub' | 'main' | 'datathon' | 'ideathon';
	title: string | null;
	quest_date: string;
	graded_count: number;
	total_students: number;
}

// GET /facilitator/quests/{id}/students response item
export interface ScoreOut {
	id: string;
	quest_id: string;
	legacy_student_id: number;
	student_name: string;
	score: number | null;
	is_submitted: boolean;
}

// POST /facilitator/quests/{id}/scores request item
export interface ScoreEntry {
	legacy_student_id: number;
	score: number | null;
	is_submitted?: boolean;
}

// GET /student/courses/{id}/scores — scores array item
export interface StudentScoreRow {
	quest_id: string;
	quest_number: number;
	quest_type: string;
	title: string | null;
	quest_date: string;
	score: number | null;
	is_submitted: boolean;
}

// Bonus score
export interface BonusScoreOut {
	id: string;
	cached_course_id: number;
	legacy_student_id: number;
	student_name: string;
	score: number;
	category: string;
	reason: string;
	given_by_name: string;
	given_at: string;
}

// GET /student/courses/{id}/scores full response
export interface CourseScoreSummary {
	legacy_course_id: number;
	course_name: string;
	scores: StudentScoreRow[];
	bonus_scores: BonusScoreOut[];
	total_quest_score: number;
	total_bonus_score: number;
	total_score: number;
}

export const SCORE_RULES: Record<string, { min: number; max: number; step: number }> = {
	sub: { min: 0, max: 1, step: 1 },
	main: { min: 0, max: 5, step: 1 },
	datathon: { min: 0, max: 10, step: 0.5 },
	ideathon: { min: 0, max: 20, step: 0.5 }
};

export const QUEST_TYPE_LABELS: Record<string, string> = {
	sub: '서브퀘스트',
	main: '메인퀘스트',
	datathon: '데이터톤',
	ideathon: '아이디어톤'
};

export interface RubricItemOut {
	rubric_metric: string;
	rubric_order: number | null;
	human_score: number | null;
	gpt_score: number | null;
	feedback: string | null;
}

export interface TaskRubricOut {
	task_title: string;
	rubric_items: RubricItemOut[];
	overall_feedback: string | null;
	total_human: number;
	total_gpt: number;
	max_score: number;
	is_graded: boolean;
}

export interface StudentRubricResponse {
	legacy_course_id: number;
	course_name: string;
	student_name: string;
	tasks: TaskRubricOut[];
	total_rubric_tasks: number;
}

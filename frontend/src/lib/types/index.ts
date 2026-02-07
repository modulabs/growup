export interface User {
	legacy_user_id: number;
	name: string;
	role: 'student' | 'facilitator';
}

export interface CourseInfo {
	legacy_course_id: number;
	name: string;
	cohort: string;
	category: string;
}

export interface LoginResponse {
	access_token: string;
	token_type: string;
	legacy_user_id: number;
	name: string;
	role: 'student' | 'facilitator';
	active_courses: CourseInfo[];
}

export interface Course {
	legacy_course_id: number;
	name: string;
	cohort: string;
	category: string;
	is_active: boolean;
}

export interface Student {
	legacy_user_id: number;
	name: string;
}

export interface Quest {
	id: string;
	cached_course_id: number;
	quest_number: number;
	quest_type: 'sub' | 'main' | 'datathon' | 'ideathon';
	title: string | null;
	quest_date: string;
	created_at: string;
	updated_at: string;
}

export interface QuestScore {
	id: string;
	quest_id: string;
	legacy_student_id: number;
	student_name: string;
	score: number | null;
	is_submitted: boolean;
	graded_at: string | null;
}

export interface ScoreEntry {
	legacy_student_id: number;
	score: number | null;
	is_submitted: boolean;
}

export interface CourseScoreSummary {
	course: CourseInfo;
	quests: Quest[];
	scores: QuestScore[];
	total_score: number | null;
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

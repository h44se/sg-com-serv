export interface Meeting {
  meeting_key: number;
  meeting_name: string;
  meeting_official_name: string | null;
  location: string | null;
  country_code: string | null;
  country_name: string | null;
}

export interface Session {
  session_key: number;
  meeting_key: number;
  session_name: string;
  session_type: string;
  date_start_utc: string;
  date_end_utc: string | null;
}

export interface PositionSample {
  date_utc: string;
  session_key: number;
  meeting_key: number;
  driver_number: number;
  position: number;
}

export interface LapSample {
  meeting_key: number;
  session_key: number;
  driver_number: number;
  lap_number: number;
  date_start_utc: string | null;
  payload: Record<string, unknown>;
}

export interface RaceControlMessage {
  meeting_key: number | null;
  session_key: number | null;
  date_utc: string;
  category: string | null;
  message: string;
}

export interface ClassificationRow {
  position: number | null;
  driver_number: number | null;
  driver_name: string | null;
  team_name: string | null;
  points: number | null;
  status: string | null;
}

export interface WeatherForecastDay {
  date: string;
  label: string;
  summary: string;
  is_wet: boolean;
  precipitation_probability_max: number | null;
  precipitation_sum_mm: number | null;
  rain_sum_mm: number | null;
  showers_sum_mm: number | null;
  snowfall_sum_mm: number | null;
  temperature_max_c: number | null;
  temperature_min_c: number | null;
}

export interface VenueContext {
  circuit_name: string;
  circuit_short_name: string | null;
  circuit_image_url: string | null;
  circuit_wiki_url: string | null;
  track_map_svg: string | null;
  track_length_km: number | null;
  fastest_lap_seconds: number | null;
  average_pit_stop_seconds: number | null;
  weather_forecast: WeatherForecastDay[];
}

export interface ChampionshipStandingRow {
  position: number | null;
  competitor_name: string;
  points: number;
  wins: number | null;
  gap: string | null;
}

export interface DashboardSnapshot {
  meeting: Meeting | null;
  sessions: Session[];
  latest_positions: PositionSample[];
  latest_laps: LapSample[];
  race_control: RaceControlMessage[];
  latest_results: ClassificationRow[];
  driver_standings: ChampionshipStandingRow[];
  constructor_standings: ChampionshipStandingRow[];
  venue: VenueContext | null;
  generated_at_utc: string;
}

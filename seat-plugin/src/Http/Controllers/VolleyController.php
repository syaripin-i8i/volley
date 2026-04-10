<?php

declare(strict_types=1);

namespace Volley\SeatVolley\Http\Controllers;

use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Routing\Controller;
use Illuminate\Support\Collection;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Route;
use Illuminate\Http\Client\Response;
use Illuminate\View\View;

class VolleyController extends Controller
{
    public function index(Request $request): View
    {
        $characters = $this->getAvailableCharacters();
        $selectedCharacterId = $request->query('character_id');
        $characterId = $this->resolveSelectedCharacterId($selectedCharacterId, $characters);
        $skills = collect();

        if ($characterId !== null) {
            $skills = $this->fetchCharacterSkills((int) $characterId)
                ->map(fn ($skill): array => [
                    'type_id' => (int) ($skill->skill_id ?? $skill->type_id ?? 0),
                    'level' => max(0, min(5, (int) ($skill->trained_skill_level ?? $skill->active_skill_level ?? 0))),
                ])
                ->filter(fn (array $skill): bool => $skill['type_id'] > 0)
                ->values();
        }

        return view('volley::volley.index', [
            'character_id' => $characterId,
            'characters' => $characters->values(),
            'skills' => $skills,
            'seat_home_url' => $this->resolveSeatHomeUrl(),
            'endpoints' => [
                'calculate' => route('volley.calculate'),
                'resolve_fit' => route('volley.fit.resolve'),
                'import_zkill' => route('volley.fit.import_zkill'),
            ],
        ]);
    }

    public function calculate(Request $request): JsonResponse
    {
        $engineUrl = rtrim((string) config('volley.engine_url', 'http://volley-engine:8000'), '/');
        $payload = $request->all();

        try {
            $graphResponse = Http::timeout(30)
                ->acceptJson()
                ->post($engineUrl . '/calc/graph', $payload);
            $dpsResponse = Http::timeout(30)
                ->acceptJson()
                ->post($engineUrl . '/calc/dps', $payload);
        } catch (\Throwable $exception) {
            return response()->json([
                'error' => 'Failed to reach volley-engine.',
                'message' => $exception->getMessage(),
            ], 502);
        }

        if (! $graphResponse->successful()) {
            return response()->json([
                'error' => 'volley-engine returned an error.',
                'status' => $graphResponse->status(),
                'body' => $graphResponse->json() ?? $graphResponse->body(),
            ], 502);
        }

        $body = $graphResponse->json();
        if ($dpsResponse->successful()) {
            $body['summary'] = $dpsResponse->json();
        }

        return response()->json($body, 200);
    }

    public function resolveFit(Request $request): JsonResponse
    {
        $eftText = (string) $request->input('eft_text', '');
        if (trim($eftText) === '') {
            return response()->json([
                'error' => 'EFT text is empty.',
            ], 422);
        }

        return $this->forwardEngineRequest('/fit/resolve', ['eft_text' => $eftText], 15);
    }

    public function importZkill(Request $request): JsonResponse
    {
        $url = trim((string) $request->input('url', ''));
        if ($url === '') {
            return response()->json([
                'error' => 'zKill URL is empty.',
            ], 422);
        }

        return $this->forwardEngineRequest('/fit/import-zkill', ['url' => $url], 25);
    }

    private function fetchCharacterSkills(int $characterId): Collection
    {
        $candidateModels = [
            \Seat\Eveapi\Models\Character\CharacterSkill::class,
            \Seat\Eveapi\Models\Skills\CharacterSkill::class,
            \Seat\Eveapi\Models\Character\Skills\CharacterSkill::class,
        ];

        foreach ($candidateModels as $modelClass) {
            if (! class_exists($modelClass)) {
                continue;
            }
            return $modelClass::where('character_id', $characterId)->get();
        }

        return collect();
    }

    private function getAvailableCharacters(): Collection
    {
        $user = Auth::user();
        if (! $user) {
            return collect();
        }

        $characters = collect();

        if (method_exists($user, 'characters')) {
            $characters = $user->characters()->get();
        } elseif (method_exists($user, 'all_characters')) {
            $characters = $user->all_characters();
        }

        $mainCharacterId = (int) ($user->main_character_id ?? 0);

        return $characters
            ->map(function ($character) use ($mainCharacterId): array {
                $characterId = (int) ($character->character_id ?? 0);
                $name = trim((string) ($character->name ?? $character->character_name ?? ''));

                return [
                    'character_id' => $characterId,
                    'name' => $name !== '' ? $name : (string) $characterId,
                    'is_main' => $mainCharacterId > 0 && $mainCharacterId === $characterId,
                ];
            })
            ->filter(fn (array $character): bool => $character['character_id'] > 0)
            ->unique('character_id')
            ->sortBy([
                fn (array $character): int => $character['is_main'] ? 0 : 1,
                fn (array $character): string => strtolower($character['name']),
            ])
            ->values();
    }

    private function resolveSelectedCharacterId(mixed $selectedCharacterId, Collection $characters): ?int
    {
        if ($selectedCharacterId === null || $selectedCharacterId === '') {
            return null;
        }

        $characterId = (int) $selectedCharacterId;
        if ($characterId <= 0) {
            return null;
        }

        $allowedIds = $characters->pluck('character_id')->all();

        return in_array($characterId, $allowedIds, true) ? $characterId : null;
    }

    private function forwardEngineRequest(string $path, array $payload, int $timeoutSeconds = 20): JsonResponse
    {
        $engineUrl = rtrim((string) config('volley.engine_url', 'http://volley-engine:8000'), '/');

        try {
            $response = Http::timeout($timeoutSeconds)
                ->acceptJson()
                ->post($engineUrl . $path, $payload);
        } catch (\Throwable $exception) {
            return response()->json([
                'error' => 'Failed to reach volley-engine.',
                'message' => $exception->getMessage(),
            ], 502);
        }

        if (! $response->successful()) {
            return $this->buildEngineErrorResponse($response);
        }

        return response()->json($response->json(), 200);
    }

    private function buildEngineErrorResponse(Response $response): JsonResponse
    {
        $body = $response->json();
        $status = $response->status();
        $detail = null;
        if (is_array($body)) {
            $detail = $body['detail'] ?? $body['message'] ?? $body['error'] ?? null;
        }

        return response()->json([
            'error' => 'volley-engine returned an error.',
            'status' => $status,
            'message' => $detail ?: ($response->body() ?: 'Unexpected engine error.'),
            'body' => $body ?: $response->body(),
        ], $status >= 400 && $status < 600 ? $status : 502);
    }

    private function resolveSeatHomeUrl(): string
    {
        $routeCandidates = [
            'web.home',
            'dashboard.index',
            'dashboard',
            'home',
        ];

        foreach ($routeCandidates as $name) {
            if (! Route::has($name)) {
                continue;
            }

            try {
                return route($name);
            } catch (\Throwable) {
                continue;
            }
        }

        return url('/');
    }
}

<?php

declare(strict_types=1);

namespace Volley\SeatVolley\Http\Controllers;

use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Routing\Controller;
use Illuminate\Support\Collection;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Auth;
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
}

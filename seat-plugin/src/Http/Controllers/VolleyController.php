<?php

declare(strict_types=1);

namespace Volley\SeatVolley\Http\Controllers;

use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Routing\Controller;
use Illuminate\Support\Collection;
use Illuminate\Support\Facades\Http;
use Illuminate\View\View;

class VolleyController extends Controller
{
    public function index(int $character_id): View
    {
        $skills = $this->fetchCharacterSkills($character_id)
            ->map(function ($skill): array {
                $typeId = (int) ($skill->skill_id ?? $skill->type_id ?? 0);
                $level = (int) ($skill->trained_skill_level ?? $skill->active_skill_level ?? $skill->level ?? 0);

                return [
                    'type_id' => $typeId,
                    'level' => max(0, min(5, $level)),
                ];
            })
            ->filter(fn (array $skill): bool => $skill['type_id'] > 0)
            ->values();

        return view('volley::volley.index', [
            'character_id' => $character_id,
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
}

<?php

declare(strict_types=1);

namespace Volley\SeatVolley;

use Illuminate\Support\Facades\Event;
use Illuminate\Support\ServiceProvider;

class VolleyServiceProvider extends ServiceProvider
{
    public function boot(): void
    {
        $this->mergeConfigFrom(__DIR__ . '/Config/volley.php', 'volley');
        $this->loadRoutesFrom(__DIR__ . '/../routes/web.php');
        $this->loadViewsFrom(__DIR__ . '/../resources/views', 'volley');

        $this->registerSidebarMenu();
    }

    private function registerSidebarMenu(): void
    {
        // Best-effort integration with SeAT sidebar event API.
        if (! class_exists(\Seat\Web\Events\SidebarBuilding::class)) {
            return;
        }

        Event::listen(\Seat\Web\Events\SidebarBuilding::class, function ($event): void {
            if (! method_exists($event, 'add')) {
                return;
            }

            $event->add([
                'name' => 'Damage Calc',
                'icon' => 'fa fa-crosshairs',
                'permission' => 'web',
                'route' => 'volley.index',
                'params' => ['character_id' => request()->route('character_id')],
                'parent' => 'character',
            ]);
        });
    }
}

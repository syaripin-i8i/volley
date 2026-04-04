<?php

declare(strict_types=1);

namespace Volley\SeatVolley;

use Seat\Services\AbstractSeatPlugin;

class VolleyServiceProvider extends AbstractSeatPlugin
{
    public function boot(): void
    {
        $this->loadRoutesFrom(__DIR__ . '/../routes/web.php');
        $this->loadViewsFrom(__DIR__ . '/../resources/views', 'volley');
        $this->publishes([
            __DIR__ . '/../resources/assets' => public_path('vendor/seat-volley'),
        ], 'public');
    }

    public function register(): void
    {
        $this->mergeConfigFrom(__DIR__ . '/Config/volley.php', 'volley');
        $this->mergeConfigFrom(__DIR__ . '/Config/volley.sidebar.php', 'package.sidebar');
        $this->registerPermissions(__DIR__ . '/Config/Permissions/volley.permissions.php', 'volley');
    }

    public function getName(): string
    {
        return 'Volley';
    }

    public function getPackageRepositoryUrl(): string
    {
        return 'https://github.com/syaripin-i8i/seat-volley';
    }

    public function getPackagistPackageName(): string
    {
        return 'seat-volley';
    }

    public function getPackagistVendorName(): string
    {
        return 'syaripin-i8i';
    }
}
